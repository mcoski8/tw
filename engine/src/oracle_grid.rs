//! Full Oracle Grid: persist all 105 setting EVs for every canonical hand.
//!
//! Decision 043 (Session 23) replaced heuristic mining with brute-force
//! ground-truth computation. For every canonical 7-card hand, we run Monte
//! Carlo over all 105 settings against the realistic-human mixture profile
//! and persist the full 105-EV vector — not just the argmax. The resulting
//! grid is the substrate for the Query Harness, which lets the user pose
//! poker-domain questions directly to the data.
//!
//! File format (mirrors best_response.rs's design — fixed-width records,
//! header-then-records, append-only with resume semantics):
//!   - Magic "TWOG" + version + samples + base_seed + canonical_total +
//!     opp_model_tag = 32-byte header.
//!   - Each record: u32 canonical_id + [f32; 105] EVs = 4 + 420 = 424 bytes.
//!   - Records emitted in setting-index order (matches `all_settings(hand)`),
//!     not sorted-by-EV order, so the Query Harness can index directly.
//!
//! Storage: ~6.0M canonical hands × 424 B = ~2.55 GB uncompressed. Fits
//! comfortably in RAM for whole-grid Python loaders.

use std::fs::{File, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::Path;

use rand::rngs::SmallRng;
use rand::SeedableRng;
use rayon::prelude::*;

use crate::bucketing::{bytes_to_hand, HAND_SIZE};
use crate::hand_eval::Evaluator;
use crate::monte_carlo::{mc_evaluate_all_settings, OpponentModel};
use crate::setting::{all_settings, NUM_SETTINGS};

pub const OG_MAGIC: [u8; 4] = *b"TWOG";
pub const OG_VERSION: u32 = 1;
pub const OG_HEADER_SIZE: u64 = 32;
/// 4 bytes canonical_id + NUM_SETTINGS × 4 bytes EV = 4 + 420 = 424.
pub const OG_RECORD_SIZE: u64 = 4 + (NUM_SETTINGS as u64) * 4;

/// One row of the grid file: a canonical-hand id and all 105 setting EVs in
/// `all_settings(hand)` order. Setting index `i` corresponds to `all[i]`.
#[derive(Clone, Debug)]
pub struct OracleGridRecord {
    pub canonical_id: u32,
    pub evs: [f32; NUM_SETTINGS],
}

impl OracleGridRecord {
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut b = Vec::with_capacity(OG_RECORD_SIZE as usize);
        b.extend_from_slice(&self.canonical_id.to_le_bytes());
        for v in &self.evs {
            b.extend_from_slice(&v.to_le_bytes());
        }
        b
    }

    pub fn from_bytes(b: &[u8]) -> Self {
        debug_assert_eq!(b.len(), OG_RECORD_SIZE as usize);
        let mut id = [0u8; 4];
        id.copy_from_slice(&b[0..4]);
        let canonical_id = u32::from_le_bytes(id);
        let mut evs = [0f32; NUM_SETTINGS];
        for i in 0..NUM_SETTINGS {
            let off = 4 + i * 4;
            let mut v = [0u8; 4];
            v.copy_from_slice(&b[off..off + 4]);
            evs[i] = f32::from_le_bytes(v);
        }
        OracleGridRecord {
            canonical_id,
            evs,
        }
    }
}

/// Header describing the grid run. The opp_model_tag is the same scheme as
/// best_response.rs (see `opp_tag_from_model` in main.rs); for the
/// realistic-human mixture it's tag 8.
#[derive(Copy, Clone, Debug, PartialEq)]
pub struct OgHeader {
    pub version: u32,
    pub samples: u32,
    pub base_seed: u64,
    pub canonical_total: u64,
    pub opp_model_tag: u32,
    pub reserved: u32,
}

impl OgHeader {
    pub fn to_bytes(&self) -> [u8; 32] {
        let mut b = [0u8; 32];
        b[0..4].copy_from_slice(&OG_MAGIC);
        b[4..8].copy_from_slice(&self.version.to_le_bytes());
        b[8..12].copy_from_slice(&self.samples.to_le_bytes());
        b[12..20].copy_from_slice(&self.base_seed.to_le_bytes());
        b[20..28].copy_from_slice(&self.canonical_total.to_le_bytes());
        b[28..32].copy_from_slice(&self.opp_model_tag.to_le_bytes());
        b
    }

    pub fn from_bytes(b: &[u8; 32]) -> Result<Self, OgError> {
        if b[0..4] != OG_MAGIC {
            return Err(OgError::BadMagic);
        }
        let mut u32buf = [0u8; 4];
        let mut u64buf = [0u8; 8];
        u32buf.copy_from_slice(&b[4..8]);
        let version = u32::from_le_bytes(u32buf);
        u32buf.copy_from_slice(&b[8..12]);
        let samples = u32::from_le_bytes(u32buf);
        u64buf.copy_from_slice(&b[12..20]);
        let base_seed = u64::from_le_bytes(u64buf);
        u64buf.copy_from_slice(&b[20..28]);
        let canonical_total = u64::from_le_bytes(u64buf);
        u32buf.copy_from_slice(&b[28..32]);
        let opp_model_tag = u32::from_le_bytes(u32buf);
        Ok(OgHeader {
            version,
            samples,
            base_seed,
            canonical_total,
            opp_model_tag,
            reserved: 0,
        })
    }
}

#[derive(Debug)]
pub enum OgError {
    Io(std::io::Error),
    BadMagic,
    VersionMismatch { expected: u32, got: u32 },
    HeaderMismatch,
    TruncatedRecord,
}

impl std::fmt::Display for OgError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            OgError::Io(e) => write!(f, "io: {e}"),
            OgError::BadMagic => write!(f, "bad magic — not an oracle-grid file"),
            OgError::VersionMismatch { expected, got } => {
                write!(f, "version mismatch: expected {expected}, got {got}")
            }
            OgError::HeaderMismatch => {
                write!(f, "header does not match caller's settings (samples / seed / model)")
            }
            OgError::TruncatedRecord => write!(f, "file size is not header + N × record_size"),
        }
    }
}

impl std::error::Error for OgError {}

impl From<std::io::Error> for OgError {
    fn from(e: std::io::Error) -> Self {
        OgError::Io(e)
    }
}

/// Append-only writer for the oracle-grid file. Same resume semantics as
/// `BrWriter` in best_response.rs: re-opening with a matching header yields a
/// `resume_from` count so the caller can skip already-computed records.
pub struct OgWriter {
    file: File,
    header: OgHeader,
    pub resume_from: u64,
}

impl OgWriter {
    pub fn open_or_create(path: &Path, header: OgHeader) -> Result<Self, OgError> {
        if let Some(parent) = path.parent() {
            if !parent.as_os_str().is_empty() {
                std::fs::create_dir_all(parent)?;
            }
        }
        let mut file = OpenOptions::new()
            .create(true)
            .read(true)
            .write(true)
            .open(path)?;

        let len = file.metadata()?.len();
        let resume_from = if len == 0 {
            file.write_all(&header.to_bytes())?;
            0u64
        } else {
            if len < OG_HEADER_SIZE {
                return Err(OgError::TruncatedRecord);
            }
            let mut hbytes = [0u8; 32];
            file.seek(SeekFrom::Start(0))?;
            file.read_exact(&mut hbytes)?;
            let existing = OgHeader::from_bytes(&hbytes)?;
            if existing.version != OG_VERSION {
                return Err(OgError::VersionMismatch {
                    expected: OG_VERSION,
                    got: existing.version,
                });
            }
            if existing.samples != header.samples
                || existing.base_seed != header.base_seed
                || existing.canonical_total != header.canonical_total
                || existing.opp_model_tag != header.opp_model_tag
            {
                return Err(OgError::HeaderMismatch);
            }
            let data_len = len - OG_HEADER_SIZE;
            if data_len % OG_RECORD_SIZE != 0 {
                return Err(OgError::TruncatedRecord);
            }
            file.seek(SeekFrom::End(0))?;
            data_len / OG_RECORD_SIZE
        };

        Ok(OgWriter {
            file,
            header,
            resume_from,
        })
    }

    pub fn header(&self) -> &OgHeader {
        &self.header
    }

    /// Append a batch of records in canonical_id order. Coalesced into a
    /// single write_all to minimise syscalls.
    pub fn append(&mut self, records: &[OracleGridRecord]) -> Result<(), OgError> {
        let mut buf = Vec::with_capacity(records.len() * OG_RECORD_SIZE as usize);
        for r in records {
            buf.extend_from_slice(&r.to_bytes());
        }
        self.file.write_all(&buf)?;
        Ok(())
    }

    /// fsync — call after each block flush, NOT after every append.
    pub fn flush(&mut self) -> Result<(), OgError> {
        self.file.flush()?;
        self.file.sync_data()?;
        Ok(())
    }
}

/// Read the entire grid file into memory. Useful for small/test files; for
/// the 2.5 GB production grid, callers should mmap or stream — see the
/// Python query-harness loader.
pub fn read_all(path: &Path) -> Result<(OgHeader, Vec<OracleGridRecord>), OgError> {
    let mut file = File::open(path)?;
    let len = file.metadata()?.len();
    if len < OG_HEADER_SIZE {
        return Err(OgError::TruncatedRecord);
    }
    let mut hbytes = [0u8; 32];
    file.read_exact(&mut hbytes)?;
    let header = OgHeader::from_bytes(&hbytes)?;
    let data_len = len - OG_HEADER_SIZE;
    if data_len % OG_RECORD_SIZE != 0 {
        return Err(OgError::TruncatedRecord);
    }
    let n = (data_len / OG_RECORD_SIZE) as usize;
    let mut records = Vec::with_capacity(n);
    let mut rbuf = vec![0u8; OG_RECORD_SIZE as usize];
    for _ in 0..n {
        file.read_exact(&mut rbuf)?;
        records.push(OracleGridRecord::from_bytes(&rbuf));
    }
    Ok((header, records))
}

/// Compute the full 105-EV vector for one canonical hand under the chosen
/// opponent model. Per-hand seed mirrors `best_response::solve_one` so the
/// grid and BR files share their RNG stream definition.
pub fn solve_grid_one(
    ev: &Evaluator,
    canonical_bytes: &[u8; HAND_SIZE],
    canonical_id: u32,
    samples: usize,
    base_seed: u64,
    model: OpponentModel,
) -> OracleGridRecord {
    let hand = bytes_to_hand(canonical_bytes);
    let per_hand_seed = base_seed
        .wrapping_add((canonical_id as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15));
    let mut rng = SmallRng::seed_from_u64(per_hand_seed);
    let summary = mc_evaluate_all_settings(ev, hand, model, samples, &mut rng);
    // mc_evaluate_all_settings returns results sorted by EV. Remap to
    // all_settings(hand) order so setting-index i → evs[i].
    let all = all_settings(hand);
    let mut evs = [0f32; NUM_SETTINGS];
    for (i, s) in all.iter().enumerate() {
        let r = summary
            .results
            .iter()
            .find(|r| r.setting == *s)
            .expect("every enumerated setting must appear in summary");
        evs[i] = r.ev as f32;
    }
    OracleGridRecord {
        canonical_id,
        evs,
    }
}

/// Solve a contiguous slice of canonical hands, write blocks of `block_size`
/// records to disk through `writer`, and call `on_block` after each block
/// flush so the caller can render progress.
///
/// Parallelism mirrors `best_response::solve_range`: outer rayon over the
/// block, inner MC is serial. Inner-MC nesting would thrash the scheduler.
pub fn solve_grid_range<F>(
    ev: &Evaluator,
    canonical: &[[u8; HAND_SIZE]],
    start_id: u32,
    samples: usize,
    base_seed: u64,
    model: OpponentModel,
    block_size: usize,
    writer: &mut OgWriter,
    mut on_block: F,
) -> Result<u64, OgError>
where
    F: FnMut(u32, u64, std::time::Duration),
{
    assert!(block_size > 0);
    let total = canonical.len();
    let mut written: u64 = 0;
    let mut i = 0;
    while i < total {
        let end = (i + block_size).min(total);
        let t0 = std::time::Instant::now();
        let records: Vec<OracleGridRecord> = canonical[i..end]
            .par_iter()
            .enumerate()
            .map(|(k, h)| {
                let id = start_id + (i + k) as u32;
                solve_grid_one(ev, h, id, samples, base_seed, model)
            })
            .collect();
        writer.append(&records)?;
        writer.flush()?;
        let elapsed = t0.elapsed();
        let block_written = (end - i) as u64;
        written += block_written;
        on_block(start_id + end as u32, written, elapsed);
        i = end;
    }
    Ok(written)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::NamedTempFile;

    fn dummy_record(id: u32, base: f32) -> OracleGridRecord {
        let mut evs = [0f32; NUM_SETTINGS];
        for i in 0..NUM_SETTINGS {
            evs[i] = base + i as f32 * 0.001;
        }
        OracleGridRecord {
            canonical_id: id,
            evs,
        }
    }

    #[test]
    fn record_roundtrip_bytes() {
        let r = dummy_record(0xDEAD_BEEF, 1.5);
        let b = r.to_bytes();
        assert_eq!(b.len(), OG_RECORD_SIZE as usize);
        let back = OracleGridRecord::from_bytes(&b);
        assert_eq!(r.canonical_id, back.canonical_id);
        for i in 0..NUM_SETTINGS {
            assert!((r.evs[i] - back.evs[i]).abs() < 1e-6);
        }
    }

    #[test]
    fn header_roundtrip_bytes() {
        let h = OgHeader {
            version: OG_VERSION,
            samples: 1000,
            base_seed: 0xCAFE_BABE,
            canonical_total: 6_009_159,
            opp_model_tag: 8,
            reserved: 0,
        };
        let b = h.to_bytes();
        let back = OgHeader::from_bytes(&b).unwrap();
        assert_eq!(h.version, back.version);
        assert_eq!(h.samples, back.samples);
        assert_eq!(h.base_seed, back.base_seed);
        assert_eq!(h.canonical_total, back.canonical_total);
        assert_eq!(h.opp_model_tag, back.opp_model_tag);
    }

    #[test]
    fn writer_creates_file_with_header_then_appends_records() {
        let tmp = NamedTempFile::new().unwrap();
        let path = tmp.path().to_path_buf();
        drop(tmp);
        let header = OgHeader {
            version: OG_VERSION,
            samples: 100,
            base_seed: 42,
            canonical_total: 3,
            opp_model_tag: 8,
            reserved: 0,
        };
        {
            let mut w = OgWriter::open_or_create(&path, header).unwrap();
            assert_eq!(w.resume_from, 0);
            w.append(&[dummy_record(0, 1.0), dummy_record(1, 2.0)]).unwrap();
            w.flush().unwrap();
        }
        let (h, records) = read_all(&path).unwrap();
        assert_eq!(h.samples, 100);
        assert_eq!(records.len(), 2);
        assert_eq!(records[0].canonical_id, 0);
        assert!((records[1].evs[10] - 2.010).abs() < 1e-6);
        std::fs::remove_file(&path).ok();
    }

    #[test]
    fn writer_resumes_from_existing_file() {
        let tmp = NamedTempFile::new().unwrap();
        let path = tmp.path().to_path_buf();
        drop(tmp);
        let header = OgHeader {
            version: OG_VERSION,
            samples: 100,
            base_seed: 42,
            canonical_total: 5,
            opp_model_tag: 8,
            reserved: 0,
        };
        {
            let mut w = OgWriter::open_or_create(&path, header).unwrap();
            w.append(&[
                dummy_record(0, 1.0),
                dummy_record(1, 1.5),
                dummy_record(2, 2.0),
            ])
            .unwrap();
            w.flush().unwrap();
        }
        {
            let w = OgWriter::open_or_create(&path, header).unwrap();
            assert_eq!(w.resume_from, 3);
        }
        std::fs::remove_file(&path).ok();
    }

    #[test]
    fn writer_refuses_mismatched_header() {
        let tmp = NamedTempFile::new().unwrap();
        let path = tmp.path().to_path_buf();
        drop(tmp);
        let header = OgHeader {
            version: OG_VERSION,
            samples: 100,
            base_seed: 42,
            canonical_total: 5,
            opp_model_tag: 8,
            reserved: 0,
        };
        {
            let mut w = OgWriter::open_or_create(&path, header).unwrap();
            w.append(&[dummy_record(0, 1.0)]).unwrap();
            w.flush().unwrap();
        }
        let mismatched = OgHeader {
            version: OG_VERSION,
            samples: 999,
            base_seed: 42,
            canonical_total: 5,
            opp_model_tag: 8,
            reserved: 0,
        };
        match OgWriter::open_or_create(&path, mismatched) {
            Err(OgError::HeaderMismatch) => {}
            other => panic!("expected HeaderMismatch, got {:?}", other.err()),
        }
        std::fs::remove_file(&path).ok();
    }

    #[test]
    fn solve_grid_one_returns_105_finite_evs() {
        use crate::bucketing::hand_to_bytes;
        use crate::card::parse_hand;
        let ev = Evaluator::build();
        let cards = parse_hand("As Kh Qd Jc Ts 9h 2d").unwrap();
        let arr: [crate::card::Card; 7] = cards.try_into().unwrap();
        let bytes = hand_to_bytes(&arr);
        let r = solve_grid_one(&ev, &bytes, 7, 200, 123, OpponentModel::Random);
        assert_eq!(r.canonical_id, 7);
        for v in &r.evs {
            assert!(v.is_finite());
            assert!(*v >= -20.0 && *v <= 20.0, "EV out of net-points range: {}", v);
        }
    }

    #[test]
    fn solve_grid_one_consistent_with_mc_summary() {
        use crate::bucketing::hand_to_bytes;
        use crate::card::parse_hand;
        let ev = Evaluator::build();
        let cards = parse_hand("As Kh Qd Jc Ts 9h 2d").unwrap();
        let arr: [crate::card::Card; 7] = cards.try_into().unwrap();
        let bytes = hand_to_bytes(&arr);
        // The argmax over evs should equal the best setting from a fresh
        // `mc_evaluate_all_settings` call with the same per-hand seed.
        let r = solve_grid_one(&ev, &bytes, 7, 200, 123, OpponentModel::Random);
        let per_hand_seed = 123u64.wrapping_add((7u64).wrapping_mul(0x9E37_79B9_7F4A_7C15));
        let mut rng = SmallRng::seed_from_u64(per_hand_seed);
        let summary = mc_evaluate_all_settings(&ev, bytes_to_hand(&bytes), OpponentModel::Random, 200, &mut rng);
        let argmax = (0..NUM_SETTINGS).max_by(|&a, &b| r.evs[a].partial_cmp(&r.evs[b]).unwrap()).unwrap();
        let all = all_settings(bytes_to_hand(&bytes));
        assert_eq!(all[argmax], summary.best().setting);
    }
}

//! Best-response computation + checkpointed binary output (Sprint 3).
//!
//! For every canonical 7-card hand, run Monte Carlo over all 105 settings and
//! record the setting with the highest EV against `OpponentModel::Random`.
//! Results are written to disk as a flat stream of fixed-width 9-byte records
//! preceded by a small header, so a multi-day run can be resumed after a crash
//! by checking the file length.
//!
//! Why fixed-width records rather than bincode:
//!   1. Crash safety — we can resume at (filesize - HEADER_SIZE) / RECORD_SIZE
//!      without needing to parse any prior state.
//!   2. Deterministic ordering — canonical_id matches file position, so
//!      consumers can mmap and index directly.
//!   3. No bincode framing overhead to worry about for a 130MB+ output.
//!
//! Parallelism policy (sprint prompt #5): the OUTER loop over canonical hands
//! is rayon-parallel. The inner Monte Carlo uses the SERIAL
//! `mc_evaluate_all_settings` — coarse outer chunks beat nested work-stealing
//! here because the inner kernel is short (<50 ms) and nesting would thrash
//! the scheduler.

use std::fs::{File, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::Path;

use rand::rngs::SmallRng;
use rand::SeedableRng;
use rayon::prelude::*;

use crate::bucketing::{bytes_to_hand, HAND_SIZE};
use crate::hand_eval::Evaluator;
use crate::monte_carlo::{mc_evaluate_all_settings, McSummary, OpponentModel};
use crate::setting::{all_settings, HandSetting};

pub const BR_MAGIC: [u8; 4] = *b"TWBR";
pub const BR_VERSION: u32 = 1;
pub const BR_HEADER_SIZE: u64 = 32;
pub const BR_RECORD_SIZE: u64 = 9; // u32 + u8 + f32

/// One row of the best-response file: the chosen setting index and its EV.
/// `canonical_id` identifies the canonical hand by its position in the
/// enumeration; `best_setting_index` is an index into `all_settings(hand)`.
#[derive(Copy, Clone, Debug, PartialEq)]
pub struct BestResponseRecord {
    pub canonical_id: u32,
    pub best_setting_index: u8,
    pub best_ev: f32,
}

impl BestResponseRecord {
    pub fn to_bytes(&self) -> [u8; 9] {
        let mut b = [0u8; 9];
        b[0..4].copy_from_slice(&self.canonical_id.to_le_bytes());
        b[4] = self.best_setting_index;
        b[5..9].copy_from_slice(&self.best_ev.to_le_bytes());
        b
    }

    pub fn from_bytes(b: &[u8; 9]) -> Self {
        let mut id = [0u8; 4];
        id.copy_from_slice(&b[0..4]);
        let mut ev = [0u8; 4];
        ev.copy_from_slice(&b[5..9]);
        BestResponseRecord {
            canonical_id: u32::from_le_bytes(id),
            best_setting_index: b[4],
            best_ev: f32::from_le_bytes(ev),
        }
    }
}

/// Header written once at the start of a best-response file. The numbers here
/// pin down the run's parameters so a reader can refuse to keep appending to
/// a file that was produced with different settings.
#[derive(Copy, Clone, Debug)]
pub struct BrHeader {
    pub version: u32,
    pub samples: u32,
    pub base_seed: u64,
    pub canonical_total: u64,
    pub opp_model_tag: u32, // 0 = Random
    pub reserved: u32,
}

impl BrHeader {
    pub fn to_bytes(&self) -> [u8; 32] {
        let mut b = [0u8; 32];
        b[0..4].copy_from_slice(&BR_MAGIC);
        b[4..8].copy_from_slice(&self.version.to_le_bytes());
        b[8..12].copy_from_slice(&self.samples.to_le_bytes());
        b[12..20].copy_from_slice(&self.base_seed.to_le_bytes());
        b[20..28].copy_from_slice(&self.canonical_total.to_le_bytes());
        b[28..32].copy_from_slice(&self.opp_model_tag.to_le_bytes());
        b
    }

    pub fn from_bytes(b: &[u8; 32]) -> Result<Self, BrError> {
        if b[0..4] != BR_MAGIC {
            return Err(BrError::BadMagic);
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
        Ok(BrHeader {
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
pub enum BrError {
    Io(std::io::Error),
    BadMagic,
    VersionMismatch { expected: u32, got: u32 },
    HeaderMismatch,
    TruncatedRecord,
}

impl std::fmt::Display for BrError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            BrError::Io(e) => write!(f, "io: {e}"),
            BrError::BadMagic => write!(f, "bad magic — not a best-response file"),
            BrError::VersionMismatch { expected, got } => {
                write!(f, "version mismatch: expected {expected}, got {got}")
            }
            BrError::HeaderMismatch => {
                write!(f, "header does not match caller's settings (samples / seed / model)")
            }
            BrError::TruncatedRecord => write!(f, "file size is not header + N × record_size"),
        }
    }
}

impl std::error::Error for BrError {}

impl From<std::io::Error> for BrError {
    fn from(e: std::io::Error) -> Self {
        BrError::Io(e)
    }
}

/// Append-only writer for a best-response file.
///
/// On `open_or_create`, the file is opened with create + read + write:
///   - If empty: the provided header is written at offset 0.
///   - If non-empty: the existing header is read and compared against the
///     caller's header; on mismatch we refuse to append. The "records
///     already present" count is returned so the caller knows where to resume.
pub struct BrWriter {
    file: File,
    header: BrHeader,
    pub resume_from: u64,
}

impl BrWriter {
    pub fn open_or_create(path: &Path, header: BrHeader) -> Result<Self, BrError> {
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
            if len < BR_HEADER_SIZE {
                return Err(BrError::TruncatedRecord);
            }
            let mut hbytes = [0u8; 32];
            file.seek(SeekFrom::Start(0))?;
            file.read_exact(&mut hbytes)?;
            let existing = BrHeader::from_bytes(&hbytes)?;
            if existing.version != BR_VERSION {
                return Err(BrError::VersionMismatch {
                    expected: BR_VERSION,
                    got: existing.version,
                });
            }
            if existing.samples != header.samples
                || existing.base_seed != header.base_seed
                || existing.canonical_total != header.canonical_total
                || existing.opp_model_tag != header.opp_model_tag
            {
                return Err(BrError::HeaderMismatch);
            }
            let data_len = len - BR_HEADER_SIZE;
            if data_len % BR_RECORD_SIZE != 0 {
                return Err(BrError::TruncatedRecord);
            }
            // Position at EOF for append.
            file.seek(SeekFrom::End(0))?;
            data_len / BR_RECORD_SIZE
        };

        Ok(BrWriter {
            file,
            header,
            resume_from,
        })
    }

    pub fn header(&self) -> &BrHeader {
        &self.header
    }

    /// Append a batch of records. Records must be supplied in
    /// canonical_id order; we don't re-sort here.
    pub fn append(&mut self, records: &[BestResponseRecord]) -> Result<(), BrError> {
        // Coalesce into one write_all call to minimize syscalls.
        let mut buf = Vec::with_capacity(records.len() * BR_RECORD_SIZE as usize);
        for r in records {
            buf.extend_from_slice(&r.to_bytes());
        }
        self.file.write_all(&buf)?;
        Ok(())
    }

    /// fsync the file — call after finishing a checkpoint chunk. Not called
    /// inside `append` itself because tight inner loops would stall on fsync.
    pub fn flush(&mut self) -> Result<(), BrError> {
        self.file.flush()?;
        self.file.sync_data()?;
        Ok(())
    }
}

/// Read every record from a best-response file in order. For small files and
/// spot-checks; streaming iteration can be added if a consumer needs it.
pub fn read_all(path: &Path) -> Result<(BrHeader, Vec<BestResponseRecord>), BrError> {
    let mut file = File::open(path)?;
    let len = file.metadata()?.len();
    if len < BR_HEADER_SIZE {
        return Err(BrError::TruncatedRecord);
    }
    let mut hbytes = [0u8; 32];
    file.read_exact(&mut hbytes)?;
    let header = BrHeader::from_bytes(&hbytes)?;
    let data_len = len - BR_HEADER_SIZE;
    if data_len % BR_RECORD_SIZE != 0 {
        return Err(BrError::TruncatedRecord);
    }
    let n = (data_len / BR_RECORD_SIZE) as usize;
    let mut records = Vec::with_capacity(n);
    let mut rbuf = [0u8; 9];
    for _ in 0..n {
        file.read_exact(&mut rbuf)?;
        records.push(BestResponseRecord::from_bytes(&rbuf));
    }
    Ok((header, records))
}

/// Compute the best-response record for a single canonical hand.
///
/// Uses the SERIAL `mc_evaluate_all_settings` — see parallelism policy in the
/// module docstring. The per-hand RNG seed is `base_seed ^ canonical_id`
/// rotated, so each hand's sample stream is independent AND reproducible.
pub fn solve_one(
    ev: &Evaluator,
    canonical_bytes: &[u8; HAND_SIZE],
    canonical_id: u32,
    samples: usize,
    base_seed: u64,
    model: OpponentModel,
) -> BestResponseRecord {
    let hand = bytes_to_hand(canonical_bytes);
    let per_hand_seed = base_seed
        .wrapping_add((canonical_id as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15));
    let mut rng = SmallRng::seed_from_u64(per_hand_seed);
    let summary: McSummary =
        mc_evaluate_all_settings(ev, hand, model, samples, &mut rng);
    let best = summary.best();
    // `summary.results` is sorted by EV, but we need the index into the
    // ORIGINAL `all_settings(hand)` order so Sprint 5's trainer can
    // reconstruct the concrete setting from its canonical hand.
    let all = all_settings(hand);
    let best_idx = find_setting_index(&all, &best.setting);
    BestResponseRecord {
        canonical_id,
        best_setting_index: best_idx as u8,
        best_ev: best.ev as f32,
    }
}

fn find_setting_index(all: &[HandSetting], target: &HandSetting) -> usize {
    // Equality on HandSetting is derived from its fields; since both `all`
    // and `target` originate from `all_settings(hand)` with the same input
    // ordering, a direct position_of match is safe.
    all.iter()
        .position(|s| s == target)
        .expect("target setting must come from the same all_settings() list")
}

/// Orchestrate solving a contiguous slice of canonical hands and stream the
/// results through a `BrWriter`. Records are computed in rayon-parallel
/// blocks of `block_size`, then flushed in order.
///
/// Returns the number of records written during this call.
pub fn solve_range<F>(
    ev: &Evaluator,
    canonical: &[[u8; HAND_SIZE]],
    start_id: u32,
    samples: usize,
    base_seed: u64,
    model: OpponentModel,
    block_size: usize,
    writer: &mut BrWriter,
    mut on_block: F,
) -> Result<u64, BrError>
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
        let records: Vec<BestResponseRecord> = canonical[i..end]
            .par_iter()
            .enumerate()
            .map(|(k, h)| {
                let id = start_id + (i + k) as u32;
                solve_one(ev, h, id, samples, base_seed, model)
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
    use std::io::Seek;
    use tempfile::NamedTempFile;

    #[test]
    fn record_roundtrip_bytes() {
        let r = BestResponseRecord {
            canonical_id: 0xDEAD_BEEF,
            best_setting_index: 42,
            best_ev: 3.14159,
        };
        let b = r.to_bytes();
        let back = BestResponseRecord::from_bytes(&b);
        assert_eq!(r, back);
    }

    #[test]
    fn header_roundtrip_bytes() {
        let h = BrHeader {
            version: BR_VERSION,
            samples: 1000,
            base_seed: 0xCAFE_BABE,
            canonical_total: 12_345_678,
            opp_model_tag: 0,
            reserved: 0,
        };
        let b = h.to_bytes();
        let back = BrHeader::from_bytes(&b).unwrap();
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
        drop(tmp); // Close handle; we want to open it ourselves.
        let header = BrHeader {
            version: BR_VERSION,
            samples: 100,
            base_seed: 42,
            canonical_total: 3,
            opp_model_tag: 0,
            reserved: 0,
        };
        {
            let mut w = BrWriter::open_or_create(&path, header).unwrap();
            assert_eq!(w.resume_from, 0);
            w.append(&[
                BestResponseRecord { canonical_id: 0, best_setting_index: 0, best_ev: 1.0 },
                BestResponseRecord { canonical_id: 1, best_setting_index: 1, best_ev: 2.0 },
            ])
            .unwrap();
            w.flush().unwrap();
        }
        let (h, records) = read_all(&path).unwrap();
        assert_eq!(h.samples, 100);
        assert_eq!(records.len(), 2);
        assert_eq!(records[0].canonical_id, 0);
        assert_eq!(records[1].best_setting_index, 1);
        std::fs::remove_file(&path).ok();
    }

    #[test]
    fn writer_resumes_from_existing_file() {
        let tmp = NamedTempFile::new().unwrap();
        let path = tmp.path().to_path_buf();
        drop(tmp);
        let header = BrHeader {
            version: BR_VERSION,
            samples: 100,
            base_seed: 42,
            canonical_total: 5,
            opp_model_tag: 0,
            reserved: 0,
        };
        {
            let mut w = BrWriter::open_or_create(&path, header).unwrap();
            w.append(&[
                BestResponseRecord { canonical_id: 0, best_setting_index: 0, best_ev: 1.0 },
                BestResponseRecord { canonical_id: 1, best_setting_index: 2, best_ev: 1.5 },
                BestResponseRecord { canonical_id: 2, best_setting_index: 4, best_ev: 2.0 },
            ])
            .unwrap();
            w.flush().unwrap();
        }
        {
            let w = BrWriter::open_or_create(&path, header).unwrap();
            assert_eq!(w.resume_from, 3);
        }
        std::fs::remove_file(&path).ok();
    }

    #[test]
    fn writer_refuses_mismatched_header() {
        let tmp = NamedTempFile::new().unwrap();
        let path = tmp.path().to_path_buf();
        drop(tmp);
        let header = BrHeader {
            version: BR_VERSION,
            samples: 100,
            base_seed: 42,
            canonical_total: 5,
            opp_model_tag: 0,
            reserved: 0,
        };
        {
            let mut w = BrWriter::open_or_create(&path, header).unwrap();
            w.append(&[BestResponseRecord {
                canonical_id: 0,
                best_setting_index: 0,
                best_ev: 1.0,
            }])
            .unwrap();
            w.flush().unwrap();
        }
        let mismatched = BrHeader {
            version: BR_VERSION,
            samples: 999, // different
            base_seed: 42,
            canonical_total: 5,
            opp_model_tag: 0,
            reserved: 0,
        };
        match BrWriter::open_or_create(&path, mismatched) {
            Err(BrError::HeaderMismatch) => {}
            other => panic!("expected HeaderMismatch, got {:?}", other.err()),
        }
        std::fs::remove_file(&path).ok();
    }

    #[test]
    fn writer_refuses_truncated_record() {
        // Create a file with header + 1.5 records — odd size should be rejected.
        let tmp = NamedTempFile::new().unwrap();
        let path = tmp.path().to_path_buf();
        drop(tmp);
        let header = BrHeader {
            version: BR_VERSION,
            samples: 100,
            base_seed: 42,
            canonical_total: 5,
            opp_model_tag: 0,
            reserved: 0,
        };
        {
            let mut f = OpenOptions::new()
                .create(true)
                .write(true)
                .truncate(true)
                .open(&path)
                .unwrap();
            f.write_all(&header.to_bytes()).unwrap();
            // Write one full record + 3 bytes of a second.
            f.write_all(&BestResponseRecord {
                canonical_id: 0,
                best_setting_index: 1,
                best_ev: 1.0,
            }
            .to_bytes())
            .unwrap();
            f.write_all(&[0u8, 1, 2]).unwrap();
            f.seek(SeekFrom::Start(0)).unwrap();
        }
        match BrWriter::open_or_create(&path, header) {
            Err(BrError::TruncatedRecord) => {}
            other => panic!("expected TruncatedRecord, got {:?}", other.err()),
        }
        std::fs::remove_file(&path).ok();
    }

    #[test]
    fn solve_one_returns_valid_setting_index() {
        use crate::bucketing::hand_to_bytes;
        use crate::card::parse_hand;
        let ev = Evaluator::build();
        let cards = parse_hand("As Kh Qd Jc Ts 9h 2d").unwrap();
        let arr: [crate::card::Card; 7] = cards.try_into().unwrap();
        let bytes = hand_to_bytes(&arr);
        let rec = solve_one(&ev, &bytes, 7, 200, 123, OpponentModel::Random);
        assert!(rec.best_setting_index < 105);
        // Use f32 not f64 — records are stored as f32. Net points are bounded
        // [-20, 20], so f32 covers the range.
        assert!(rec.best_ev.is_finite());
        assert!(rec.best_ev >= -20.0 && rec.best_ev <= 20.0);
        assert_eq!(rec.canonical_id, 7);
    }
}

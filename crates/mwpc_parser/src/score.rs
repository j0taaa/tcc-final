//! Exact ordering of non-negative binary64 sums, in units of 2^-1074.
//!
//! This is independent of Python's rational reference implementation. Public
//! weights remain f64; only the comparison key uses an arbitrary-size integer.

use num_bigint::BigUint;
use num_traits::ToPrimitive;

#[derive(Clone, Debug, Default, Eq, Ord, PartialEq, PartialOrd)]
pub(crate) struct ExactScore(BigUint);

impl ExactScore {
    // Caller validates finite, non-negative input at the public boundary.
    pub fn from_float(value: f64) -> Self {
        let bits = value.to_bits();
        let exponent = (bits >> 52) & 0x7ff;
        let fraction = bits & ((1_u64 << 52) - 1);
        if exponent == 0 {
            Self(BigUint::from(fraction))
        } else {
            Self(BigUint::from(fraction | (1_u64 << 52)) << (exponent - 1) as usize)
        }
    }

    pub fn sum(terms: &[f64]) -> Self {
        terms.iter().fold(Self::default(), |sum, value| {
            sum.add(&Self::from_float(*value))
        })
    }

    pub fn add(&self, other: &Self) -> Self {
        Self(&self.0 + &other.0)
    }

    /// One correctly rounded conversion, including subnormals and ties to even.
    pub fn to_float(&self) -> f64 {
        let bits = self.0.bits();
        if bits <= 52 {
            return f64::from_bits(self.0.to_u64().unwrap_or(0));
        }
        let shift = (bits - 53) as usize;
        let mut mantissa = (&self.0 >> shift).to_u64().expect("53-bit mantissa");
        if shift > 0 {
            let half = BigUint::from(1_u8) << (shift - 1);
            let remainder = &self.0 - (BigUint::from(mantissa) << shift);
            if remainder > half || (remainder == half && mantissa & 1 == 1) {
                mantissa += 1;
            }
        }
        let mut exponent = bits - 52;
        if mantissa == 1_u64 << 53 {
            mantissa >>= 1;
            exponent += 1;
        }
        if exponent >= 0x7ff {
            return f64::INFINITY;
        }
        f64::from_bits((exponent << 52) | (mantissa & ((1_u64 << 52) - 1)))
    }
}

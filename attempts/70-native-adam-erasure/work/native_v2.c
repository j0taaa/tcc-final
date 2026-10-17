#include <fenv.h>
#include <float.h>
#include <math.h>
#include <stdint.h>

typedef struct { float w, m, v; } State;
typedef struct { float a, d; } Coeff;

int a70_v2_init_fp(void) {
    if (fesetenv(FE_DFL_ENV) || fesetround(FE_TONEAREST)) return 0;
    if (FLT_RADIX != 2 || FLT_MANT_DIG != 24 || FLT_EVAL_METHOD != 0
        || sizeof(float) != 4 || sizeof(State) != 12 || sizeof(Coeff) != 8)
        return 0;
    volatile float tiny = nextafterf(0.0f, 1.0f);
    volatile float one = 1.0f;
    return tiny > 0.0f && tiny * one == tiny;
}

void a70_v2_make_schedule(Coeff *out, int size, float eta, float b1, float b2) {
    out[0] = (Coeff){0.0f, 0.0f};
    for (int t = 1; t < size; ++t) {
        float p1 = powf(b1, (float)t);
        float p2 = powf(b2, (float)t);
        float c1 = 1.0f - p1;
        float c2 = 1.0f - p2;
        out[t] = (Coeff){eta / c1, sqrtf(c2)};
    }
}

State a70_v2_moments(State s, float g, float b1, float b2) {
    float c1 = 1.0f - b1;
    float c2 = 1.0f - b2;
    float bm = b1 * s.m;
    float cg = c1 * g;
    float bv = b2 * s.v;
    float cg2 = c2 * g;
    float gg = cg2 * g;
    s.m = bm + cg;
    s.v = bv + gg;
    return s;
}

State a70_v2_weight(State s, Coeff c, float eps) {
    float root = sqrtf(s.v);
    float scaled = root / c.d;
    float denom = scaled + eps;
    float numerator = c.a * s.m;
    float update = numerator / denom;
    s.w = s.w - update;
    return s;
}

State a70_v2_step(State s, float g, Coeff c, float b1, float b2, float eps) {
    return a70_v2_weight(a70_v2_moments(s, g, b1, b2), c, eps);
}

State a70_v2_run_zero(State s, int first, int count, const Coeff *table,
               float b1, float b2, float eps) {
    for (int i = 0; i < count; ++i)
        s = a70_v2_step(s, 0.0f, table[first + i], b1, b2, eps);
    return s;
}

State a70_v2_decay(State s, int count, float b1, float b2) {
    for (int i = 0; i < count; ++i) s = a70_v2_moments(s, 0.0f, b1, b2);
    return s;
}

float a70_v2_update_bound(float a, float m, float eps) {
    float numerator = a * fabsf(m);
    return numerator / eps;
}

float a70_v2_sub_round(float w, float u) { return w - u; }
float a70_v2_add_round(float x, float y) { return x + y; }
float a70_v2_mul_round(float x, float y) { return x * y; }
float a70_v2_div_round(float x, float y) { return x / y; }
float a70_v2_sqrt_round(float x) { return sqrtf(x); }

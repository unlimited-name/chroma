#ifndef __RANDOM_H__
#define __RANDOM_H__

#include <curand_kernel.h>

#include "physical_constants.h"
#include "interpolate.h"

__device__ float
uniform(curandState *s, const float &low, const float &high)
{
    return low + curand_uniform(s)*(high-low);
}

__device__ float3
uniform_sphere(curandState *s)
{
    float theta = uniform(s, 0.0f, 2*PI);
    float u = uniform(s, -1.0f, 1.0f);
    float c = sqrtf(1.0f-u*u);

    return make_float3(c*cosf(theta), c*sinf(theta), u);
}

// Draw a random sample given a cumulative distribution function
// Assumptions: ncdf >= 2, cdf_y[0] is 0.0, and cdf_y[ncdf-1] is 1.0
__device__ float
sample_cdf(curandState *rng, int ncdf, float *cdf_x, float *cdf_y)
{
    return interp(curand_uniform(rng),ncdf,cdf_y,cdf_x);
}

// Sample from a uniformly-sampled CDF
__device__ float
sample_cdf(curandState *rng, int ncdf, float x0, float delta, float *cdf_y)
{
    float u = curand_uniform(rng);

    int lower = 0;
    int upper = ncdf - 1;

    while(lower < upper-1)
    {
	int half = (lower + upper) / 2;

	if (u < cdf_y[half])
	    upper = half;
	else
	    lower = half;
    }
  
    float delta_cdf_y = cdf_y[upper] - cdf_y[lower];

    return x0 + delta*lower + delta*(u-cdf_y[lower])/delta_cdf_y;
}

extern "C"
{

__global__ void
init_rng(int nthreads, curandState *s, unsigned long long seed,
	 unsigned long long offset)
{
    int id = blockIdx.x*blockDim.x + threadIdx.x;

    if (id >= nthreads)
	return;

    curand_init(seed, id, offset, &s[id]);
}

__global__ void
fill_uniform(int nthreads, curandState *s, float *a, float low, float high)
{
    int id = blockIdx.x*blockDim.x + threadIdx.x;

    if (id >= nthreads)
	return;

    a[id] = uniform(&s[id], low, high);

}

__global__ void
fill_uniform_sphere(int nthreads, curandState *s, float3 *a)
{
    int id = blockIdx.x*blockDim.x + threadIdx.x;

    if (id >= nthreads)
	return;

    a[id] = uniform_sphere(&s[id]);
}

__global__ void
fill_sample_cdf(int offset, int nthreads, curandState *rng_states,
		int ncdf, float *cdf_x,	float *cdf_y, float *x)
{
    int id = blockIdx.x*blockDim.x + threadIdx.x;

    if (id >= nthreads)
	return;

    curandState *s = rng_states+id;

    x[id+offset] = sample_cdf(s,ncdf,cdf_x,cdf_y);
}

} // extern "c"

#endif

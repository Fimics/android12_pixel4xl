/*
 * Copyright © 2016 Red Hat.
 * Copyright © 2016 Bas Nieuwenhuizen
 *
 * based on amdgpu winsys.
 * Copyright © 2011 Marek Olšák <maraeo@gmail.com>
 * Copyright © 2015 Advanced Micro Devices, Inc.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice (including the next
 * paragraph) shall be included in all copies or substantial portions of the
 * Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
 * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */

#include <stdio.h>

#include "radv_amdgpu_bo.h"

#include <amdgpu.h>
#include "drm-uapi/amdgpu_drm.h"
#include <inttypes.h>
#include <pthread.h>
#include <unistd.h>

#include "util/u_atomic.h"
#include "util/u_memory.h"
#include "util/u_math.h"

static void radv_amdgpu_winsys_bo_destroy(struct radeon_winsys_bo *_bo);

static int
radv_amdgpu_bo_va_op(struct radv_amdgpu_winsys *ws,
		     amdgpu_bo_handle bo,
		     uint64_t offset,
		     uint64_t size,
		     uint64_t addr,
		     uint32_t bo_flags,
		     uint64_t internal_flags,
		     uint32_t ops)
{
	uint64_t flags = internal_flags;
	if (bo) {
		flags = AMDGPU_VM_PAGE_READABLE |
		         AMDGPU_VM_PAGE_EXECUTABLE;

		if ((bo_flags & RADEON_FLAG_VA_UNCACHED) &&
		    ws->info.chip_class >= GFX9)
			flags |= AMDGPU_VM_MTYPE_UC;

		if (!(bo_flags & RADEON_FLAG_READ_ONLY))
			flags |= AMDGPU_VM_PAGE_WRITEABLE;
	}

	size = align64(size, getpagesize());

	return amdgpu_bo_va_op_raw(ws->dev, bo, offset, size, addr,
				   flags, ops);
}

static void
radv_amdgpu_winsys_virtual_map(struct radv_amdgpu_winsys_bo *bo,
                               const struct radv_amdgpu_map_range *range)
{
	uint64_t internal_flags = 0;
	assert(range->size);

	if (!range->bo) {
		if (!bo->ws->info.has_sparse_vm_mappings)
			return;

		internal_flags |= AMDGPU_VM_PAGE_PRT;
	} else
		p_atomic_inc(&range->bo->ref_count);

	int r = radv_amdgpu_bo_va_op(bo->ws, range->bo ? range->bo->bo : NULL,
				     range->bo_offset, range->size,
				     range->offset + bo->base.va, 0,
				     internal_flags, AMDGPU_VA_OP_MAP);
	if (r)
		abort();
}

static void
radv_amdgpu_winsys_virtual_unmap(struct radv_amdgpu_winsys_bo *bo,
                                 const struct radv_amdgpu_map_range *range)
{
	uint64_t internal_flags = 0;
	assert(range->size);

	if (!range->bo) {
		if(!bo->ws->info.has_sparse_vm_mappings)
			return;

		/* Even though this is an unmap, if we don't set this flag,
		   AMDGPU is going to complain about the missing buffer. */
		internal_flags |= AMDGPU_VM_PAGE_PRT;
	}

	int r = radv_amdgpu_bo_va_op(bo->ws, range->bo ? range->bo->bo : NULL,
				     range->bo_offset, range->size,
				     range->offset + bo->base.va, 0, internal_flags,
				     AMDGPU_VA_OP_UNMAP);
	if (r)
		abort();

	if (range->bo)
		radv_amdgpu_winsys_bo_destroy((struct radeon_winsys_bo *)range->bo);
}

static int bo_comparator(const void *ap, const void *bp) {
	struct radv_amdgpu_bo *a = *(struct radv_amdgpu_bo *const *)ap;
	struct radv_amdgpu_bo *b = *(struct radv_amdgpu_bo *const *)bp;
	return (a > b) ? 1 : (a < b) ? -1 : 0;
}

static VkResult
radv_amdgpu_winsys_rebuild_bo_list(struct radv_amdgpu_winsys_bo *bo)
{
	if (bo->bo_capacity < bo->range_count) {
		uint32_t new_count = MAX2(bo->bo_capacity * 2, bo->range_count);
		struct radv_amdgpu_winsys_bo **bos =
			realloc(bo->bos, new_count * sizeof(struct radv_amdgpu_winsys_bo *));
		if (!bos)
			return VK_ERROR_OUT_OF_HOST_MEMORY;
		bo->bos = bos;
		bo->bo_capacity = new_count;
	}

	uint32_t temp_bo_count = 0;
	for (uint32_t i = 0; i < bo->range_count; ++i)
		if (bo->ranges[i].bo)
			bo->bos[temp_bo_count++] = bo->ranges[i].bo;

	qsort(bo->bos, temp_bo_count, sizeof(struct radv_amdgpu_winsys_bo *), &bo_comparator);

	uint32_t final_bo_count = 1;
	for (uint32_t i = 1; i < temp_bo_count; ++i)
		if (bo->bos[i] != bo->bos[i - 1])
			bo->bos[final_bo_count++] = bo->bos[i];

	bo->bo_count = final_bo_count;

	return VK_SUCCESS;
}

static VkResult
radv_amdgpu_winsys_bo_virtual_bind(struct radeon_winsys_bo *_parent,
                                   uint64_t offset, uint64_t size,
                                   struct radeon_winsys_bo *_bo, uint64_t bo_offset)
{
	struct radv_amdgpu_winsys_bo *parent = (struct radv_amdgpu_winsys_bo *)_parent;
	struct radv_amdgpu_winsys_bo *bo = (struct radv_amdgpu_winsys_bo*)_bo;
	int range_count_delta, new_idx;
	int first = 0, last;
	struct radv_amdgpu_map_range new_first, new_last;
	VkResult result;

	assert(parent->is_virtual);
	assert(!bo || !bo->is_virtual);

	/* We have at most 2 new ranges (1 by the bind, and another one by splitting a range that contains the newly bound range). */
	if (parent->range_capacity - parent->range_count < 2) {
		uint32_t range_capacity = parent->range_capacity + 2;
		struct radv_amdgpu_map_range *ranges =
			realloc(parent->ranges,
				range_capacity * sizeof(struct radv_amdgpu_map_range));
		if (!ranges)
			return VK_ERROR_OUT_OF_HOST_MEMORY;
		parent->ranges = ranges;
		parent->range_capacity = range_capacity;
	}

	/*
	 * [first, last] is exactly the range of ranges that either overlap the
	 * new parent, or are adjacent to it. This corresponds to the bind ranges
	 * that may change.
	 */
	while(first + 1 < parent->range_count && parent->ranges[first].offset + parent->ranges[first].size < offset)
		++first;

	last = first;
	while(last + 1 < parent->range_count && parent->ranges[last + 1].offset <= offset + size)
		++last;

	/* Whether the first or last range are going to be totally removed or just
	 * resized/left alone. Note that in the case of first == last, we will split
	 * this into a part before and after the new range. The remove flag is then
	 * whether to not create the corresponding split part. */
	bool remove_first = parent->ranges[first].offset == offset;
	bool remove_last = parent->ranges[last].offset + parent->ranges[last].size == offset + size;
	bool unmapped_first = false;

	assert(parent->ranges[first].offset <= offset);
	assert(parent->ranges[last].offset + parent->ranges[last].size >= offset + size);

	/* Try to merge the new range with the first range. */
	if (parent->ranges[first].bo == bo && (!bo || offset - bo_offset == parent->ranges[first].offset - parent->ranges[first].bo_offset)) {
		size += offset - parent->ranges[first].offset;
		offset = parent->ranges[first].offset;
		bo_offset = parent->ranges[first].bo_offset;
		remove_first = true;
	}

	/* Try to merge the new range with the last range. */
	if (parent->ranges[last].bo == bo && (!bo || offset - bo_offset == parent->ranges[last].offset - parent->ranges[last].bo_offset)) {
		size = parent->ranges[last].offset + parent->ranges[last].size - offset;
		remove_last = true;
	}

	range_count_delta = 1 - (last - first + 1) + !remove_first + !remove_last;
	new_idx = first + !remove_first;

	/* Any range between first and last is going to be entirely covered by the new range so just unmap them. */
	for (int i = first + 1; i < last; ++i)
		radv_amdgpu_winsys_virtual_unmap(parent, parent->ranges + i);

	/* If the first/last range are not left alone we unmap then and optionally map
	 * them again after modifications. Not that this implicitly can do the splitting
	 * if first == last. */
	new_first = parent->ranges[first];
	new_last = parent->ranges[last];

	if (parent->ranges[first].offset + parent->ranges[first].size > offset || remove_first) {
		radv_amdgpu_winsys_virtual_unmap(parent, parent->ranges + first);
		unmapped_first = true;

		if (!remove_first) {
			new_first.size = offset - new_first.offset;
			radv_amdgpu_winsys_virtual_map(parent, &new_first);
		}
	}

	if (parent->ranges[last].offset < offset + size || remove_last) {
		if (first != last || !unmapped_first)
			radv_amdgpu_winsys_virtual_unmap(parent, parent->ranges + last);

		if (!remove_last) {
			new_last.size -= offset + size - new_last.offset;
			new_last.bo_offset += (offset + size - new_last.offset);
			new_last.offset = offset + size;
			radv_amdgpu_winsys_virtual_map(parent, &new_last);
		}
	}

	/* Moves the range list after last to account for the changed number of ranges. */
	memmove(parent->ranges + last + 1 + range_count_delta, parent->ranges + last + 1,
	        sizeof(struct radv_amdgpu_map_range) * (parent->range_count - last - 1));

	if (!remove_first)
		parent->ranges[first] = new_first;

	if (!remove_last)
		parent->ranges[new_idx + 1] = new_last;

	/* Actually set up the new range. */
	parent->ranges[new_idx].offset = offset;
	parent->ranges[new_idx].size = size;
	parent->ranges[new_idx].bo = bo;
	parent->ranges[new_idx].bo_offset = bo_offset;

	radv_amdgpu_winsys_virtual_map(parent, parent->ranges + new_idx);

	parent->range_count += range_count_delta;

	result = radv_amdgpu_winsys_rebuild_bo_list(parent);
	if (result != VK_SUCCESS)
		return result;

	return VK_SUCCESS;
}

static void radv_amdgpu_winsys_bo_destroy(struct radeon_winsys_bo *_bo)
{
	struct radv_amdgpu_winsys_bo *bo = radv_amdgpu_winsys_bo(_bo);
	struct radv_amdgpu_winsys *ws = bo->ws;

	if (p_atomic_dec_return(&bo->ref_count))
		return;
	if (bo->is_virtual) {
		for (uint32_t i = 0; i < bo->range_count; ++i) {
			radv_amdgpu_winsys_virtual_unmap(bo, bo->ranges + i);
		}
		free(bo->bos);
		free(bo->ranges);
	} else {
		if (bo->ws->debug_all_bos) {
			u_rwlock_wrlock(&bo->ws->global_bo_list_lock);
			list_del(&bo->global_list_item);
			bo->ws->num_buffers--;
			u_rwlock_wrunlock(&bo->ws->global_bo_list_lock);
		}
		radv_amdgpu_bo_va_op(bo->ws, bo->bo, 0, bo->size, bo->base.va,
				     0, 0, AMDGPU_VA_OP_UNMAP);
		amdgpu_bo_free(bo->bo);
	}

	if (bo->initial_domain & RADEON_DOMAIN_VRAM) {
		if (bo->base.vram_no_cpu_access) {
			p_atomic_add(&ws->allocated_vram,
				     -align64(bo->size, ws->info.gart_page_size));
		} else {
			p_atomic_add(&ws->allocated_vram_vis,
				     -align64(bo->size, ws->info.gart_page_size));
		}
	}

	if (bo->initial_domain & RADEON_DOMAIN_GTT)
		p_atomic_add(&ws->allocated_gtt,
			     -align64(bo->size, ws->info.gart_page_size));

	amdgpu_va_range_free(bo->va_handle);
	FREE(bo);
}

static void radv_amdgpu_add_buffer_to_global_list(struct radv_amdgpu_winsys_bo *bo)
{
	struct radv_amdgpu_winsys *ws = bo->ws;

	if (bo->ws->debug_all_bos) {
		u_rwlock_wrlock(&ws->global_bo_list_lock);
		list_addtail(&bo->global_list_item, &ws->global_bo_list);
		ws->num_buffers++;
		u_rwlock_wrunlock(&ws->global_bo_list_lock);
	}
}

static struct radeon_winsys_bo *
radv_amdgpu_winsys_bo_create(struct radeon_winsys *_ws,
			     uint64_t size,
			     unsigned alignment,
			     enum radeon_bo_domain initial_domain,
			     unsigned flags,
			     unsigned priority)
{
	struct radv_amdgpu_winsys *ws = radv_amdgpu_winsys(_ws);
	struct radv_amdgpu_winsys_bo *bo;
	struct amdgpu_bo_alloc_request request = {0};
	struct radv_amdgpu_map_range *ranges = NULL;
	amdgpu_bo_handle buf_handle;
	uint64_t va = 0;
	amdgpu_va_handle va_handle;
	int r;
	bo = CALLOC_STRUCT(radv_amdgpu_winsys_bo);
	if (!bo) {
		return NULL;
	}

	unsigned virt_alignment = alignment;
	if (size >= ws->info.pte_fragment_size)
		virt_alignment = MAX2(virt_alignment, ws->info.pte_fragment_size);

	r = amdgpu_va_range_alloc(ws->dev, amdgpu_gpu_va_range_general,
				  size, virt_alignment, 0, &va, &va_handle,
				  (flags & RADEON_FLAG_32BIT ? AMDGPU_VA_RANGE_32_BIT : 0) |
				   AMDGPU_VA_RANGE_HIGH);
	if (r)
		goto error_va_alloc;

	bo->base.va = va;
	bo->va_handle = va_handle;
	bo->size = size;
	bo->ws = ws;
	bo->is_virtual = !!(flags & RADEON_FLAG_VIRTUAL);
	bo->ref_count = 1;

	if (flags & RADEON_FLAG_VIRTUAL) {
		ranges = realloc(NULL, sizeof(struct radv_amdgpu_map_range));
		if (!ranges)
			goto error_ranges_alloc;

		bo->ranges = ranges;
		bo->range_count = 1;
		bo->range_capacity = 1;

		bo->ranges[0].offset = 0;
		bo->ranges[0].size = size;
		bo->ranges[0].bo = NULL;
		bo->ranges[0].bo_offset = 0;

		radv_amdgpu_winsys_virtual_map(bo, bo->ranges);
		return (struct radeon_winsys_bo *)bo;
	}

	request.alloc_size = size;
	request.phys_alignment = alignment;

	if (initial_domain & RADEON_DOMAIN_VRAM) {
		request.preferred_heap |= AMDGPU_GEM_DOMAIN_VRAM;

		/* Since VRAM and GTT have almost the same performance on
		 * APUs, we could just set GTT. However, in order to decrease
		 * GTT(RAM) usage, which is shared with the OS, allow VRAM
		 * placements too. The idea is not to use VRAM usefully, but
		 * to use it so that it's not unused and wasted.
		 */
		if (!ws->info.has_dedicated_vram)
			request.preferred_heap |= AMDGPU_GEM_DOMAIN_GTT;
	}

	if (initial_domain & RADEON_DOMAIN_GTT)
		request.preferred_heap |= AMDGPU_GEM_DOMAIN_GTT;
	if (initial_domain & RADEON_DOMAIN_GDS)
		request.preferred_heap |= AMDGPU_GEM_DOMAIN_GDS;
	if (initial_domain & RADEON_DOMAIN_OA)
		request.preferred_heap |= AMDGPU_GEM_DOMAIN_OA;

	if (flags & RADEON_FLAG_CPU_ACCESS)
		request.flags |= AMDGPU_GEM_CREATE_CPU_ACCESS_REQUIRED;
	if (flags & RADEON_FLAG_NO_CPU_ACCESS) {
		bo->base.vram_no_cpu_access = initial_domain & RADEON_DOMAIN_VRAM;
		request.flags |= AMDGPU_GEM_CREATE_NO_CPU_ACCESS;
	}
	if (flags & RADEON_FLAG_GTT_WC)
		request.flags |= AMDGPU_GEM_CREATE_CPU_GTT_USWC;
	if (!(flags & RADEON_FLAG_IMPLICIT_SYNC) && ws->info.drm_minor >= 22)
		request.flags |= AMDGPU_GEM_CREATE_EXPLICIT_SYNC;
	if (flags & RADEON_FLAG_NO_INTERPROCESS_SHARING &&
	    ws->info.has_local_buffers &&
	    (ws->use_local_bos || (flags & RADEON_FLAG_PREFER_LOCAL_BO))) {
		bo->base.is_local = true;
		request.flags |= AMDGPU_GEM_CREATE_VM_ALWAYS_VALID;
	}

	/* this won't do anything on pre 4.9 kernels */
	if (initial_domain & RADEON_DOMAIN_VRAM) {
		if (ws->zero_all_vram_allocs || (flags & RADEON_FLAG_ZERO_VRAM))
			request.flags |= AMDGPU_GEM_CREATE_VRAM_CLEARED;
	}

	r = amdgpu_bo_alloc(ws->dev, &request, &buf_handle);
	if (r) {
		fprintf(stderr, "amdgpu: Failed to allocate a buffer:\n");
		fprintf(stderr, "amdgpu:    size      : %"PRIu64" bytes\n", size);
		fprintf(stderr, "amdgpu:    alignment : %u bytes\n", alignment);
		fprintf(stderr, "amdgpu:    domains   : %u\n", initial_domain);
		goto error_bo_alloc;
	}

	r = radv_amdgpu_bo_va_op(ws, buf_handle, 0, size, va, flags, 0,
				 AMDGPU_VA_OP_MAP);
	if (r)
		goto error_va_map;

	bo->bo = buf_handle;
	bo->initial_domain = initial_domain;
	bo->is_shared = false;
	bo->priority = priority;

	r = amdgpu_bo_export(buf_handle, amdgpu_bo_handle_type_kms, &bo->bo_handle);
	assert(!r);

	if (initial_domain & RADEON_DOMAIN_VRAM) {
		/* Buffers allocated in VRAM with the NO_CPU_ACCESS flag
		 * aren't mappable and they are counted as part of the VRAM
		 * counter.
		 *
		 * Otherwise, buffers with the CPU_ACCESS flag or without any
		 * of both (imported buffers) are counted as part of the VRAM
		 * visible counter because they can be mapped.
		 */
		if (bo->base.vram_no_cpu_access) {
			p_atomic_add(&ws->allocated_vram,
				     align64(bo->size, ws->info.gart_page_size));
		} else {
			p_atomic_add(&ws->allocated_vram_vis,
				     align64(bo->size, ws->info.gart_page_size));
		}
	}

	if (initial_domain & RADEON_DOMAIN_GTT)
		p_atomic_add(&ws->allocated_gtt,
			     align64(bo->size, ws->info.gart_page_size));

	radv_amdgpu_add_buffer_to_global_list(bo);
	return (struct radeon_winsys_bo *)bo;
error_va_map:
	amdgpu_bo_free(buf_handle);

error_bo_alloc:
	free(ranges);

error_ranges_alloc:
	amdgpu_va_range_free(va_handle);

error_va_alloc:
	FREE(bo);
	return NULL;
}

static void *
radv_amdgpu_winsys_bo_map(struct radeon_winsys_bo *_bo)
{
	struct radv_amdgpu_winsys_bo *bo = radv_amdgpu_winsys_bo(_bo);
	int ret;
	void *data;
	ret = amdgpu_bo_cpu_map(bo->bo, &data);
	if (ret)
		return NULL;
	return data;
}

static void
radv_amdgpu_winsys_bo_unmap(struct radeon_winsys_bo *_bo)
{
	struct radv_amdgpu_winsys_bo *bo = radv_amdgpu_winsys_bo(_bo);
	amdgpu_bo_cpu_unmap(bo->bo);
}

static uint64_t
radv_amdgpu_get_optimal_vm_alignment(struct radv_amdgpu_winsys *ws,
				     uint64_t size, unsigned alignment)
{
	uint64_t vm_alignment = alignment;

	/* Increase the VM alignment for faster address translation. */
	if (size >= ws->info.pte_fragment_size)
		vm_alignment = MAX2(vm_alignment, ws->info.pte_fragment_size);

	/* Gfx9: Increase the VM alignment to the most significant bit set
	 * in the size for faster address translation.
	 */
	if (ws->info.chip_class >= GFX9) {
		unsigned msb = util_last_bit64(size); /* 0 = no bit is set */
		uint64_t msb_alignment = msb ? 1ull << (msb - 1) : 0;

		vm_alignment = MAX2(vm_alignment, msb_alignment);
	}
	return vm_alignment;
}

static struct radeon_winsys_bo *
radv_amdgpu_winsys_bo_from_ptr(struct radeon_winsys *_ws,
                               void *pointer,
                               uint64_t size,
			       unsigned priority)
{
	struct radv_amdgpu_winsys *ws = radv_amdgpu_winsys(_ws);
	amdgpu_bo_handle buf_handle;
	struct radv_amdgpu_winsys_bo *bo;
	uint64_t va;
	amdgpu_va_handle va_handle;
	uint64_t vm_alignment;

	bo = CALLOC_STRUCT(radv_amdgpu_winsys_bo);
	if (!bo)
		return NULL;

	if (amdgpu_create_bo_from_user_mem(ws->dev, pointer, size, &buf_handle))
		goto error;

	/* Using the optimal VM alignment also fixes GPU hangs for buffers that
	 * are imported.
	 */
	vm_alignment = radv_amdgpu_get_optimal_vm_alignment(ws, size,
							    ws->info.gart_page_size);

	if (amdgpu_va_range_alloc(ws->dev, amdgpu_gpu_va_range_general,
	                          size, vm_alignment, 0, &va, &va_handle,
				  AMDGPU_VA_RANGE_HIGH))
		goto error_va_alloc;

	if (amdgpu_bo_va_op(buf_handle, 0, size, va, 0, AMDGPU_VA_OP_MAP))
		goto error_va_map;

	/* Initialize it */
	bo->base.va = va;
	bo->va_handle = va_handle;
	bo->size = size;
	bo->ref_count = 1;
	bo->ws = ws;
	bo->bo = buf_handle;
	bo->initial_domain = RADEON_DOMAIN_GTT;
	bo->priority = priority;

	ASSERTED int r = amdgpu_bo_export(buf_handle, amdgpu_bo_handle_type_kms, &bo->bo_handle);
	assert(!r);

	p_atomic_add(&ws->allocated_gtt,
		     align64(bo->size, ws->info.gart_page_size));

	radv_amdgpu_add_buffer_to_global_list(bo);
	return (struct radeon_winsys_bo *)bo;

error_va_map:
	amdgpu_va_range_free(va_handle);

error_va_alloc:
	amdgpu_bo_free(buf_handle);

error:
	FREE(bo);
	return NULL;
}

static struct radeon_winsys_bo *
radv_amdgpu_winsys_bo_from_fd(struct radeon_winsys *_ws,
			      int fd, unsigned priority,
			      uint64_t *alloc_size)
{
	struct radv_amdgpu_winsys *ws = radv_amdgpu_winsys(_ws);
	struct radv_amdgpu_winsys_bo *bo;
	uint64_t va;
	amdgpu_va_handle va_handle;
	enum amdgpu_bo_handle_type type = amdgpu_bo_handle_type_dma_buf_fd;
	struct amdgpu_bo_import_result result = {0};
	struct amdgpu_bo_info info = {0};
	enum radeon_bo_domain initial = 0;
	int r;
	bo = CALLOC_STRUCT(radv_amdgpu_winsys_bo);
	if (!bo)
		return NULL;

	r = amdgpu_bo_import(ws->dev, type, fd, &result);
	if (r)
		goto error;

	r = amdgpu_bo_query_info(result.buf_handle, &info);
	if (r)
		goto error_query;

	if (alloc_size) {
		*alloc_size = info.alloc_size;
	}

	r = amdgpu_va_range_alloc(ws->dev, amdgpu_gpu_va_range_general,
				  result.alloc_size, 1 << 20, 0, &va, &va_handle,
				  AMDGPU_VA_RANGE_HIGH);
	if (r)
		goto error_query;

	r = radv_amdgpu_bo_va_op(ws, result.buf_handle, 0, result.alloc_size,
				 va, 0, 0, AMDGPU_VA_OP_MAP);
	if (r)
		goto error_va_map;

	if (info.preferred_heap & AMDGPU_GEM_DOMAIN_VRAM)
		initial |= RADEON_DOMAIN_VRAM;
	if (info.preferred_heap & AMDGPU_GEM_DOMAIN_GTT)
		initial |= RADEON_DOMAIN_GTT;

	bo->bo = result.buf_handle;
	bo->base.va = va;
	bo->va_handle = va_handle;
	bo->initial_domain = initial;
	bo->size = result.alloc_size;
	bo->is_shared = true;
	bo->ws = ws;
	bo->priority = priority;
	bo->ref_count = 1;

	r = amdgpu_bo_export(result.buf_handle, amdgpu_bo_handle_type_kms, &bo->bo_handle);
	assert(!r);

	if (bo->initial_domain & RADEON_DOMAIN_VRAM)
		p_atomic_add(&ws->allocated_vram,
			     align64(bo->size, ws->info.gart_page_size));
	if (bo->initial_domain & RADEON_DOMAIN_GTT)
		p_atomic_add(&ws->allocated_gtt,
			     align64(bo->size, ws->info.gart_page_size));

	radv_amdgpu_add_buffer_to_global_list(bo);
	return (struct radeon_winsys_bo *)bo;
error_va_map:
	amdgpu_va_range_free(va_handle);

error_query:
	amdgpu_bo_free(result.buf_handle);

error:
	FREE(bo);
	return NULL;
}

static bool
radv_amdgpu_winsys_get_fd(struct radeon_winsys *_ws,
			  struct radeon_winsys_bo *_bo,
			  int *fd)
{
	struct radv_amdgpu_winsys_bo *bo = radv_amdgpu_winsys_bo(_bo);
	enum amdgpu_bo_handle_type type = amdgpu_bo_handle_type_dma_buf_fd;
	int r;
	unsigned handle;
	r = amdgpu_bo_export(bo->bo, type, &handle);
	if (r)
		return false;

	*fd = (int)handle;
	bo->is_shared = true;
	return true;
}

static bool
radv_amdgpu_bo_get_flags_from_fd(struct radeon_winsys *_ws, int fd,
                                 enum radeon_bo_domain *domains,
                                 enum radeon_bo_flag *flags)
{
	struct radv_amdgpu_winsys *ws = radv_amdgpu_winsys(_ws);
	struct amdgpu_bo_import_result result = {0};
	struct amdgpu_bo_info info = {0};
	int r;

	*domains = 0;
	*flags = 0;

	r = amdgpu_bo_import(ws->dev, amdgpu_bo_handle_type_dma_buf_fd, fd, &result);
	if (r)
		return false;

	r = amdgpu_bo_query_info(result.buf_handle, &info);
	amdgpu_bo_free(result.buf_handle);
	if (r)
		return false;

	if (info.preferred_heap & AMDGPU_GEM_DOMAIN_VRAM)
		*domains |= RADEON_DOMAIN_VRAM;
	if (info.preferred_heap & AMDGPU_GEM_DOMAIN_GTT)
		*domains |= RADEON_DOMAIN_GTT;
	if (info.preferred_heap & AMDGPU_GEM_DOMAIN_GDS)
		*domains |= RADEON_DOMAIN_GDS;
	if (info.preferred_heap & AMDGPU_GEM_DOMAIN_OA)
		*domains |= RADEON_DOMAIN_OA;

	if (info.alloc_flags & AMDGPU_GEM_CREATE_CPU_ACCESS_REQUIRED)
		*flags |= RADEON_FLAG_CPU_ACCESS;
	if (info.alloc_flags & AMDGPU_GEM_CREATE_NO_CPU_ACCESS)
		*flags |= RADEON_FLAG_NO_CPU_ACCESS;
	if (!(info.alloc_flags & AMDGPU_GEM_CREATE_EXPLICIT_SYNC))
		*flags |= RADEON_FLAG_IMPLICIT_SYNC;
	if (info.alloc_flags & AMDGPU_GEM_CREATE_CPU_GTT_USWC)
		*flags |= RADEON_FLAG_GTT_WC;
	if (info.alloc_flags & AMDGPU_GEM_CREATE_VM_ALWAYS_VALID)
		*flags |= RADEON_FLAG_NO_INTERPROCESS_SHARING | RADEON_FLAG_PREFER_LOCAL_BO;
	if (info.alloc_flags & AMDGPU_GEM_CREATE_VRAM_CLEARED)
		*flags |= RADEON_FLAG_ZERO_VRAM;
	return true;
}

static unsigned eg_tile_split(unsigned tile_split)
{
	switch (tile_split) {
	case 0:     tile_split = 64;    break;
	case 1:     tile_split = 128;   break;
	case 2:     tile_split = 256;   break;
	case 3:     tile_split = 512;   break;
	default:
	case 4:     tile_split = 1024;  break;
	case 5:     tile_split = 2048;  break;
	case 6:     tile_split = 4096;  break;
	}
	return tile_split;
}

static unsigned radv_eg_tile_split_rev(unsigned eg_tile_split)
{
	switch (eg_tile_split) {
	case 64:    return 0;
	case 128:   return 1;
	case 256:   return 2;
	case 512:   return 3;
	default:
	case 1024:  return 4;
	case 2048:  return 5;
	case 4096:  return 6;
	}
}

static void
radv_amdgpu_winsys_bo_set_metadata(struct radeon_winsys_bo *_bo,
				   struct radeon_bo_metadata *md)
{
	struct radv_amdgpu_winsys_bo *bo = radv_amdgpu_winsys_bo(_bo);
	struct amdgpu_bo_metadata metadata = {0};
	uint64_t tiling_flags = 0;

	if (bo->ws->info.chip_class >= GFX9) {
		tiling_flags |= AMDGPU_TILING_SET(SWIZZLE_MODE, md->u.gfx9.swizzle_mode);
		tiling_flags |= AMDGPU_TILING_SET(SCANOUT, md->u.gfx9.scanout);
	} else {
		if (md->u.legacy.macrotile == RADEON_LAYOUT_TILED)
			tiling_flags |= AMDGPU_TILING_SET(ARRAY_MODE, 4); /* 2D_TILED_THIN1 */
		else if (md->u.legacy.microtile == RADEON_LAYOUT_TILED)
			tiling_flags |= AMDGPU_TILING_SET(ARRAY_MODE, 2); /* 1D_TILED_THIN1 */
		else
			tiling_flags |= AMDGPU_TILING_SET(ARRAY_MODE, 1); /* LINEAR_ALIGNED */

		tiling_flags |= AMDGPU_TILING_SET(PIPE_CONFIG, md->u.legacy.pipe_config);
		tiling_flags |= AMDGPU_TILING_SET(BANK_WIDTH, util_logbase2(md->u.legacy.bankw));
		tiling_flags |= AMDGPU_TILING_SET(BANK_HEIGHT, util_logbase2(md->u.legacy.bankh));
		if (md->u.legacy.tile_split)
			tiling_flags |= AMDGPU_TILING_SET(TILE_SPLIT, radv_eg_tile_split_rev(md->u.legacy.tile_split));
		tiling_flags |= AMDGPU_TILING_SET(MACRO_TILE_ASPECT, util_logbase2(md->u.legacy.mtilea));
		tiling_flags |= AMDGPU_TILING_SET(NUM_BANKS, util_logbase2(md->u.legacy.num_banks)-1);

		if (md->u.legacy.scanout)
			tiling_flags |= AMDGPU_TILING_SET(MICRO_TILE_MODE, 0); /* DISPLAY_MICRO_TILING */
		else
			tiling_flags |= AMDGPU_TILING_SET(MICRO_TILE_MODE, 1); /* THIN_MICRO_TILING */
	}

	metadata.tiling_info = tiling_flags;
	metadata.size_metadata = md->size_metadata;
	memcpy(metadata.umd_metadata, md->metadata, sizeof(md->metadata));

	amdgpu_bo_set_metadata(bo->bo, &metadata);
}

static void
radv_amdgpu_winsys_bo_get_metadata(struct radeon_winsys_bo *_bo,
                                   struct radeon_bo_metadata *md)
{
	struct radv_amdgpu_winsys_bo *bo = radv_amdgpu_winsys_bo(_bo);
	struct amdgpu_bo_info info = {0};

	int r = amdgpu_bo_query_info(bo->bo, &info);
	if (r)
		return;

	uint64_t tiling_flags = info.metadata.tiling_info;

	if (bo->ws->info.chip_class >= GFX9) {
		md->u.gfx9.swizzle_mode = AMDGPU_TILING_GET(tiling_flags, SWIZZLE_MODE);
		md->u.gfx9.scanout = AMDGPU_TILING_GET(tiling_flags, SCANOUT);
	} else {
		md->u.legacy.microtile = RADEON_LAYOUT_LINEAR;
		md->u.legacy.macrotile = RADEON_LAYOUT_LINEAR;

		if (AMDGPU_TILING_GET(tiling_flags, ARRAY_MODE) == 4)  /* 2D_TILED_THIN1 */
			md->u.legacy.macrotile = RADEON_LAYOUT_TILED;
		else if (AMDGPU_TILING_GET(tiling_flags, ARRAY_MODE) == 2) /* 1D_TILED_THIN1 */
			md->u.legacy.microtile = RADEON_LAYOUT_TILED;

		md->u.legacy.pipe_config = AMDGPU_TILING_GET(tiling_flags, PIPE_CONFIG);
		md->u.legacy.bankw = 1 << AMDGPU_TILING_GET(tiling_flags, BANK_WIDTH);
		md->u.legacy.bankh = 1 << AMDGPU_TILING_GET(tiling_flags, BANK_HEIGHT);
		md->u.legacy.tile_split = eg_tile_split(AMDGPU_TILING_GET(tiling_flags, TILE_SPLIT));
		md->u.legacy.mtilea = 1 << AMDGPU_TILING_GET(tiling_flags, MACRO_TILE_ASPECT);
		md->u.legacy.num_banks = 2 << AMDGPU_TILING_GET(tiling_flags, NUM_BANKS);
		md->u.legacy.scanout = AMDGPU_TILING_GET(tiling_flags, MICRO_TILE_MODE) == 0; /* DISPLAY */
	}

	md->size_metadata = info.metadata.size_metadata;
	memcpy(md->metadata, info.metadata.umd_metadata, sizeof(md->metadata));
}

void radv_amdgpu_bo_init_functions(struct radv_amdgpu_winsys *ws)
{
	ws->base.buffer_create = radv_amdgpu_winsys_bo_create;
	ws->base.buffer_destroy = radv_amdgpu_winsys_bo_destroy;
	ws->base.buffer_map = radv_amdgpu_winsys_bo_map;
	ws->base.buffer_unmap = radv_amdgpu_winsys_bo_unmap;
	ws->base.buffer_from_ptr = radv_amdgpu_winsys_bo_from_ptr;
	ws->base.buffer_from_fd = radv_amdgpu_winsys_bo_from_fd;
	ws->base.buffer_get_fd = radv_amdgpu_winsys_get_fd;
	ws->base.buffer_set_metadata = radv_amdgpu_winsys_bo_set_metadata;
	ws->base.buffer_get_metadata = radv_amdgpu_winsys_bo_get_metadata;
	ws->base.buffer_virtual_bind = radv_amdgpu_winsys_bo_virtual_bind;
	ws->base.buffer_get_flags_from_fd = radv_amdgpu_bo_get_flags_from_fd;
}

(selector) => {
	const images = Array.from(document.querySelectorAll(selector));
	// 过滤掉没有 src 的无效图片，增加健壮性
	return images.filter(img => img.src).every(img => img.complete);
}
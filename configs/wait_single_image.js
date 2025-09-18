(selector) => {
	const img = document.querySelector(selector);
	// check if the image is loaded
	return img && img.src && img.complete;
}
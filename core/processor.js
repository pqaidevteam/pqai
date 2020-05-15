
function run(arr, mid, end, tick) {
	if (
		!Array.isArray(arr) ||
		typeof mid !== 'function' ||
		typeof end !== 'function'
	) {
		return end(null);
	}
	var ticker = typeof tick === 'function';
	var interim = [];
	var arr = arr.map(e => e);
	(function _execute() {
		if (!arr.length) end(interim);
		else {
			mid(arr.shift(), result => {
				interim.push(result);
				if (ticker) tick(arr.length, interim.length);
				setTimeout(function () {
					_execute();
				}, 0);
			});
		}
	}());
}

function runInBatch(arr, mid, end) {
	if (!Array.isArray(arr) || typeof mid !== 'function' || typeof end !== 'function') return end(null);
	var ticker = typeof tick === 'function';
	var sum = arr.length;
	var interim = [];
	var arr = arr.map(e => e);
	var threads = 0;
	var maxThreads = 4;
	(function _execute() {
		if (!arr.length)
			return;
		threads++;
		mid(arr.shift(), result => {
			threads--;
			interim.push(result);
			if (ticker) tick(interim.length, sum);
			if (arr.length === 0 && sum-arr.length-interim.length === 0)
				return end(interim);
			while (threads < maxThreads && arr.length)
				_execute();
		});
	}());
}

module.exports = {
	run,
	runInBatch
}

var LineByLineReader = require('line-by-line');

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

function runOnLines(file, mid, end) {
    lr = new LineByLineReader(file);
    let arr = [];

	lr.on('error', function (err) {
		console.log(err);
		end(false);
	});

	lr.on('line', function (line) {
		lr.pause();
		mid(line, done => {
			lr.resume();
		});
	});

	lr.on('end', function () {
		end(arr);
	});
}

function runOnLinesNonstop(file, mid, end) {
    lr = new LineByLineReader(file);
    let arr = [];

	lr.on('error', function (err) {
		console.log(err);
		end(false);
	});

	lr.on('line', function (line) {
		mid(line);
	});

	lr.on('end', function () {
		end(arr);
	});
}

function runOnCursor (cursor, mid, end) {
	let arr = [];
	(function _next (cursor) {
		cursor.hasNext().then(moreDocs => {
			if (!moreDocs) {
				end(arr);
			} else {
				cursor.next().then(doc => {
					mid(doc, res => {
						arr.push(res);
						_next(cursor);
					});
				}, err => {
					throw err;
				});
			}
		}, err => {
			throw err;
		}).catch(err => {
			throw err;
		});
	}(cursor));
}

function fc(fnArr) {
	return function (input, callback) {
		_triggerFn(0, input, result => {
			callback(result);
		});
	}
	function _triggerFn(num, input, cb) {
		if (num == fnArr.length) {
			cb(input);
		} else {
			fnArr[num](input, output => {
				_triggerFn(num+1, output, cb);
			});
		}
	}
}

module.exports = {
	run,
	runInBatch,
	fc,
	runOnCursor,
	runOnLines,
	runOnLinesNonstop
}
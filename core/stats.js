'use strict'

let genericWords = 'l p l m n v oy sa kabushiki kaisha limited publ inc incorporated corp corporation co ltd llc nv gmbh services ag bv pvt pte pty electronics licensing holding holdings technologies products beijing and patent'.split(' ');

function clean (assigneeName) {
	assigneeName = assigneeName.trim();
	let arr = assigneeName.split(/[\W+]/g).filter(e => e.trim());
	while (arr.length > 1) {
		let lastTerm = arr[arr.length-1].toLowerCase();
		if (genericWords.includes(lastTerm)) {
			arr.pop();
		} else {
			let str = arr.join(' ');
			while (str.length > 60) {
				str = str.replace(/\W+\w+$/, '');
			}
			return str;
		}
	}
	let str = arr.join(' ');
	while (str.length > 60) {
		str = str.replace(/\W+\w+$/, '');
	}
	return str;
}

function isUniversity (assigneeName) {
	if (assigneeName.match(/\b(univ|university|inst|institute)\b/i)) {
		return true;
	} else {
		return false;
	}
}

function getOScore(docs) {
	let O_score = parseInt((docs[0].distance/1.3)*100);
	return O_score;
}

function getYearStats(docs) {
	docs = docs.filter(e => typeof e.filingDate == 'string');
	let years = docs.map(e => e.filingDate).map(
		e => e.match(/\d{4}/)
	);
	return _yearDist(years);

	function _yearDist (arr) {
		let dist = _dist(arr);
		dist.sort((a, b) => parseInt(b) - parseInt(a));
		let output = {};
		dist.forEach(e => {
			output[e[0]] = e[1]; 
		});
		return output;
	}
}

function getAssigneeStats(docs) {
	docs = docs.filter(e => typeof e.assignee == 'string');
	let assignees = docs.map(e => e.assignee).map(e => clean(e));
	return _assigneeDist(assignees);

	function _assigneeDist (arr, max=6) {
		let dist = _dist(arr);
		let total = dist.reduce((a, b) => a + b[1], 0);
		let top = dist.slice(0, max-1);
		let ntop = top.reduce((a, b) => a + b[1], 0);
		let nOther = total-ntop;
		top.push(['Others', nOther]);
		let output = {};
		top.forEach(e => {
			output[e[0]] = e[1]; 
		});
		return output;
	}
}

function _dist(arr) {
	let map = {}
	arr.forEach(el => {
		if (typeof map[el] !== 'number') {
			map[el] = 0;
		}
		map[el]++
	});
	let brr = []
	for (let el in map) {
		brr.push([el, map[el]]);
	}
	brr.sort((a, b) => b[1]-a[1]);
	return brr;
}

module.exports = {
	getAssigneeStats,
	getOScore,
	getYearStats
}
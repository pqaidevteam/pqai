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

module.exports = {
	clean,
	isUniversity
}
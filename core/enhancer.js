'use strict';

const processor = require('./processor.js');
const articulator = require('./articulator.js');
const toolbox = require('./toolbox.js');
const _ = require('lodash');

function enhance (query, callback) {
	query = query.toLowerCase();
	let keywords = _.uniq(query.match(/[a-z]+/g));
	
	// remove stop words
	keywords = keywords.filter(kw => !toolbox.isGeneric(kw));

	_lemmatizeKeywords(keywords, lemmas => {
		_getSynonyms(lemmas, synonymArr => {
			let enhancedQuery = _formQuery(synonymArr);
			callback(enhancedQuery);
		});
	});

	function _lemmatizeKeywords(keywords, callback) {
		processor.run(keywords, (keyword, callback) => {
			articulator.getLemma(keyword, lemma => {
				callback(lemma);
			});
		}, arr => {
			callback(arr);
		});
	}

	function _getSynonyms(keywords, callback) {
		let used = {};
		processor.run(keywords, (keyword, callback) => {
			articulator.getLemma(keyword, keyword => {
				articulator.getSynonyms(keyword, synonyms => {
					// remove duplicates and generic
					synonyms = synonyms.filter(
						e => !used[e] && !toolbox.isGeneric(e)
					);	

					// mark remaining as used
					synonyms.forEach(e => used[e] = true);

					callback(synonyms);
				});
			});
		}, arr => {
			callback(arr);
		});
	}

	function _formQuery(arr) {
		let eq = '(';
		let subqueries =  arr.map(e => {
			if (e.length > 0) {
				return '(' + e.join(' OR ') + ')'
			} else {
				return '';
			}
		});
		eq += subqueries.join(' AND ');
		eq += ')';
		return eq;
	}	
}

module.exports = {
	enhance
}
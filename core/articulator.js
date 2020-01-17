'use strict';

const axios = require('axios');
const API_URL = 'http://127.0.0.1:5000/';

function getSynonyms (word, callback) {
	word = word.toLowerCase();
	if (!word.match(/^[a-z]+$/)) { 			// invalid word
		callback([word]);
	} else {
		let url = API_URL + 'synonyms/' + word;
		axios.get(url).then(response => {
			callback(response.data.filter(e => e[1] <= 1.15).map(e => e[0]));
		}).catch(err => {
			console.log('Unable to fetch synonyms from API.');
			callback([word]);
		});
	}
}

function getLemma (word, callback) {
	word = word.toLowerCase();
	if (!word.match(/^[a-z]+$/)) { 			// invalid word
		callback(word);
	} else {
		let url = API_URL + 'lemma/' + word;
		axios.get(url).then(response => {
			callback(response.data);
		}).catch(err => {
			console.log('Unable to fetch lemma from API.');
			callback(word);
		});
	}
}

module.exports = {
	getSynonyms
}
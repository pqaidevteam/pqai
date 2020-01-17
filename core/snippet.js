'use strict';

const axios = require('axios');
const querystring = require('querystring');
const API_URL = 'http://127.0.0.1:5000/';

function getSnippet (pn, query, callback) {
	_getSnippetFromAPI(pn, query, snippet => {
		callback(snippet);
	});

	function _getSnippetFromAPI(pn, query, callback) {
		let url = API_URL + 'snippet/';
		let postReqData = querystring.stringify({ query, pn });
		axios({
			method: 'post', url: url, data: postReqData
		}).then(response => {
			callback(response.data);
		}).catch(err => {
			console.log(err);
			callback(!err);
		});
	}
}

module.exports = {
	getSnippet
}
'use strict';

const axios = require('axios');
const querystring = require('querystring');
const processor = require('./processor.js');
const MongoClient = require('mongodb').MongoClient;
const mongoURL = 'mongodb://127.0.0.1:27017/';
const API_URL = 'http://127.0.0.1:5000/';
const options = {
	useNewUrlParser: true,
	useUnifiedTopology: true
}

let mongoClient = null;
let mongoColl = null;

(function _connectMongo() {
	MongoClient.connect(mongoURL, options, (err, client) => {
		if (err) {
			console.log("DBError: Cannot connect to Mongo DB.")
			throw err;
		}
		mongoClient = client;
		mongoColl = client.db('pqai').collection('fulltext');
	});
}());

function searchByQuery (query, indexId, callback) {
	query = query.trim().toLowerCase();

	let b64query = Buffer.from(query).toString('base64');
	let url = `${API_URL}search/${indexId}/${b64query}`;

	axios.get(url).then(response => {
		let results = response.data; 	// format: [[publicationNumber, dist]]
		_getDetails(results, detailedResults => {
			_getConfidenceScore(detailedResults, done => {
				callback(detailedResults);
			});
		});
	}).catch(err => {
		console.log(err);
		console.log('Unable to reach search API');
		callback(null);
	});
}

function searchByPatent (pn, indexId, callback) {

	let b64query = Buffer.from(pn).toString('base64');
	let url = `${API_URL}simpats/${indexId}/${b64query}`;

	axios.get(url).then(response => {
		let results = response.data; 	// format: [[publicationNumber, dist]]
		_getDetails(results, detailedResults => {
			callback(detailedResults);
		});
	}).catch(err => {
		console.log(err);
		console.log('Unable to reach search API');
		callback(null);
	});
}


function getLongList(query, indexId, callback) {
	query = query.trim().toLowerCase();
	let b64query = Buffer.from(query).toString('base64');
	let url = `${API_URL}longlist/${indexId}/${b64query}`;

	axios.get(url).then(response => {
		let results = response.data; 	// format: [[publicationNumber, dist]]
		_getDetails(results, detailedResults => {
			callback(detailedResults);
		});
	}).catch(err => {
		console.log(err);
		console.log('Unable to reach search API');
		callback(null);
	});
}

function _getDetails (results, callback) {
	let pns = results.map(e => e[0]);
	let scores = results.map(e => e[1]);
	let resObj = {};
	pns.forEach((pn, i) => {
		resObj[pn] = {
			publicationNumber: pn,
			distance: scores[i]
		}
	});

	let mongoQuery = { publicationNumber: { $in: pns } };
	let fields = {
		publicationNumber: 1,
		assignee: 1,
		app_date: 1,
		cpcs: 1
	};
	let response = mongoColl.find(mongoQuery, fields).toArray();
	response.then(docs => {
		docs.forEach(doc => {
			let pn = doc.publicationNumber;
			resObj[pn].title = doc.title;
			resObj[pn].abstract = doc.abstract;
			resObj[pn].filingDate = doc.filingDate;
			resObj[pn].assignee = doc.applicants[0];
			resObj[pn].cpcs = doc.cpcs;
		});
		let arr = [];
		for (let key in resObj) {
			arr.push(resObj[key]);
		}
		callback(arr);
	}).catch(err => {
		console.log(err);
		callback();
	});
}

function _getConfidenceScore(docs, callback) {
	let url = API_URL + 'confidence/';
	let cpcsArr = docs.map(e => {
		if (Array.isArray(e.cpcs)) {
			return e.cpcs;
		} else {
			return [];
		}
	});
	let postReqData = querystring.stringify({
		cpcs: JSON.stringify(cpcsArr)
	});

	axios({
		method: 'post', url: url, data: postReqData
	}).then(response => {
		if (typeof response.data !== 'string') {
			return callback(false);
		}
		docs.forEach(doc => {
			doc.confidence = response.data;
		});
		callback(true);
	}).catch(err => {
		// console.log(err);
		console.log('Error in getting confidence scores.');
		callback(false);
	});
}


// the function is rudimentary as of now
// may be enhanced to detect multiple patent number formats
function _isPatentQuery(txt) {
	if (txt.match(/[a-z]{3,}/i)) {	// has "words"
		return false;
	} else if (txt.match(/\d/)) { // no words but has numbers in it
		return true;
	} else {
		return false;
	}
}

module.exports = {
	searchByQuery,
	searchByPatent,
	getLongList
}
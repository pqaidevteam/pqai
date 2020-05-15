'use strict';

const express = require('express');
const hbs = require('hbs');
const compression = require('compression');
const axios = require('axios');
const bodyParser = require('body-parser');

const stats = require('./core/stats.js');

const app = express();
app.use(compression());
app.use(express.static('public'));
app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.set('view engine', 'hbs');
app.set('views', __dirname + '/views');
hbs.registerPartials(__dirname + '/views/partials');
hbs.registerHelper('floatToPercentage', function (floatVal) {
	let f = parseFloat(floatVal);
	return parseInt(100*f);
})

/*
	Routes
*/

app.get('/', function (req, res) {
	res.render('index');
});

app.get('/search', function (req, res) {
	res.render('search');
});

app.get('/b68ccabe63f8059a52604f1e6fd2e5ba', function (req, res) {
	res.render('about');
});

app.post('/mediator', function (req, res) {
	let cmd = req.body.cmd;
	if (cmd == 'search-by-patent' || cmd == 'search-by-query') {
		let query = req.body.query;
		let indexId = req.body.techDomain;
		let before = req.body.before;
		let after = req.body.after;
		let responseType = req.body.responseType || 'html';
		let url = 'http://localhost:5000/documents/';
		let params = {
			q: query,
			idx: indexId,
			before: before,
			after: after,
			n: 10,
			snip: 1
		}
		axios.get(url, { params })
		.then(response => {
			if (responseType == 'json') {
				res.send(response.data)
			} else {
				res.render('result_list', { data: response.data });
			}
		})
		.catch(err => {
			console.log(err);
			res.status(500).send(error('Error occurred.'));
		})
	
	} else if (cmd == 'get-snippet') {
		let query = req.body.query;
		let publicationNumber = req.body.publicationNumber;
		
		let url = 'http://localhost:5000/snippets/'
		let params = { q: query, pn: publicationNumber }
		axios.get(url, { params })
		.then(response => res.status(200).send(response.data))
		.catch(err => res.status(500).send(error('Error occurred.')))

	} else if (cmd == 'get-stats') {
		let query = req.body.query;
		let indexId = req.body.techDomain;
		let url = 'http://localhost:5000/documents/'
		let params = {
			q: query, idx: indexId, n: 100
		}
		axios.get(url, { params })
		.then(response => {
			let docs = response.data.results;
			console.log(docs)
			let result = {}
			result.assigneeStats = stats.getAssigneeStats(docs);
			result.yearStats = stats.getYearStats(docs);
			result.oScore = stats.getOScore(docs);
			res.status(200).send(result);
		})
		.catch(err => {
			console.log(err);
			res.status(500).send(error('Error occurred.'))
		})
	} else if (cmd == 'get-element-wise-mapping') {
		let ref = req.body.ref;
		let query = req.body.query;
		let url = 'http://localhost:5000/mappings/';
		let params = { q: query, ref: ref }
		axios.get(url, { params })
		.then(response => res.render('mapping', {mappings: response.data}))
		.catch(err => res.status(500).send(error('Error occurred.')))
	} else {
		res.status(400).send(error('Invalid request.'));
	}
});

app.get('/datasets', function (req, res) {
	res.render('datasets');
});

app.get('/datasets/:datasetName/:n', function (req, res) {
	let datasetName = req.params.datasetName;
	let n = parseInt(req.params.n);
	let url = 'http://localhost:5000/datasets/'
	let params = {
		dataset: datasetName, n: n
	}
	axios.get(url, { params })
		.then(response => {
			let datapoint = response.data;
			datapoint.similars.forEach(e => e.role = 'negative');
			datapoint.citation.role = 'positive';
			let r = parseInt(datapoint.similars.length * Math.random());
			console.log('Random number', r);
			datapoint.all = datapoint.similars.slice(0, r);
			datapoint.all = datapoint.all.concat([datapoint.citation]);
			datapoint.all = datapoint.all.concat(datapoint.similars.slice(r));
			res.render('poc', { datapoint });
		})
		.catch(err => {
			console.log(err);
			res.status(500).send(error('Error occurred.'))
		})
});

function error(msg) {
	return {
		error: true,
		message: msg
	};
}

/*
	Run
*/

const PORT = 5601
app.listen(PORT, function () {
	console.log('Server running on port', PORT);
});

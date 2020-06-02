'use strict';

const express = require('express');
const hbs = require('hbs');
const compression = require('compression');
const axios = require('axios');
const bodyParser = require('body-parser');

const processor = require('./core/processor.js');
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

app.get('/search2', function (req, res) {
	res.render('search2');
});

app.get('/tech-areas', function (req, res) {
	res.render('tech_areas');
});

app.post('/mediator', function (req, res) {
	let cmd = req.body.cmd;
	if (cmd == 'search-by-patent' || cmd == 'search-by-query') {
		let query = req.body.query;
		let indexId = req.body.techDomain;
		let before = req.body.before;
		let after = req.body.after;
		let n = req.body.n || 10;
		let mappings = req.body.mappings || -1;
		let n_mappings = (mappings == -1) ? n : mappings;

		let url = 'http://localhost:5000/documents/';
		let params = {
			q: query,
			idx: indexId,
			before: before,
			after: after,
			n: n,
			snip: 0
		}

		axios.get(url, { params })
		.then(response => {
			processor.run(
				response.data.results.slice(0, n_mappings),
				(result, callback) => {
					let url = 'http://localhost:5000/mappings/';
					let params = { q: query, ref: result.id }
					
					axios.get(url, { params })
					.then(response => {
						result.mapping = response.data;
						callback();
					}).catch(err => {
						// console.log(err);
						callback();
					})
				}, arr => {
					app.render('result_list', { data: response.data },
						(err, html) => {
							response.data.listHTML = err ? null : html;
							res.send(response.data);
						}
					)
				}
			)
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
		.then(
			response => res.send(response.data)
		).catch(err => res.status(500).send(
			error('Error occurred in Python API.')
		))
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

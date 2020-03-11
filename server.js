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
		let url = 'http://localhost:5000/documents/'
		let params = {
			q: query, idx: indexId, n: 10, cnfd: 1, bib: 1, snip: 1, dist: 1
		}
		axios.get(url, { params })
			.then(response => res.status(200).send(response.data))
			.catch(err => res.status(500).send(error('Error occurred.')))
	
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
			q: query, idx: indexId, n: 100, bib: 1
		}
		axios.get(url, { params })
			.then(response => {
				let docs = response.data.results;
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
	} else {
		res.status(400).send(error('Invalid request.'));
	}
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

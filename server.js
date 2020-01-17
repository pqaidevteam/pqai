'use strict';

/*
	General Modules
*/
const express = require('express');
const hbs = require('hbs');
const compression = require('compression');
const bodyParser = require('body-parser');
const _ = require('lodash');

/*
	Custom modules
*/
const enhancer = require('./core/enhancer.js');
const searcher = require('./core/searcher.js');
const snippet = require('./core/snippet.js');
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

app.post('/mediator', function (req, res) {
	let cmd = req.body.cmd;
	if (cmd == 'expand-query') {
		let query = req.body.query;
		enhancer.enhance(query, eq => {
			if (typeof eq !== 'string') {
				res.send(error('Server error.'));
			} else {
				res.send(eq);
			}
		});
	} else if (cmd == 'search-by-patent') {
		let pn = req.body.query;
		let indexId = req.body.techDomain;
		if (!pn.match(/^US\d{7,8}[AB]\d?$/)) {
			res.send(error('Invalid patent number.'));
			return;
		}
		searcher.searchByPatent(pn, indexId, results => {
			if (!Array.isArray(results)) {
				res.send(error('An error occurred. Please check your input.'));
			} else {
				res.send(results);
			}
		});
	} else if (cmd == 'search-by-query') {
		let query = req.body.query;
		let indexId = req.body.techDomain;
		searcher.searchByQuery(query, indexId, results => {
			if (!Array.isArray(results)) {
				res.send(error('An error occurred. Please check your input.'));
			} else {
				res.send(results);
			}
		});
	} else if (cmd == 'get-snippet') {
		let query = req.body.query;
		let publicationNumber = req.body.publicationNumber;
		snippet.getSnippet(publicationNumber, query, snippet => {
			res.send(snippet);
		});
	} else if (cmd == 'get-stats') {
		let query = req.body.query;
		let indexId = req.body.techDomain;
		stats.getStats(query, indexId, results => {
			if (results.assigneeStats) {
				res.send(results);
			} else {
				res.send(error('Error in getting stats.'));
			}
		});
	} else {
		res.send(error('Invalid request.'));
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

const PORT = 8080
app.listen(PORT, function () {
	console.log('Server running on port', PORT);
});
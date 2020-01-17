'use strict';

const STOP_WORDS = ['a', 'about', 'above', 'accompanying', 'accomplish', 'accomplished', 'accomplishes', 'accomplishing', 'accordance', 'according', 'accordingly', 'achieve', 'achieved', 'achievement', 'achieves', 'achieving', 'additionally', 'advantage', 'advantageous', 'advantageously', 'advantages', 'after', 'all', 'along', 'also', 'although', 'among', 'an', 'and', 'and/or', 'any', 'are', 'art', 'as', 'aspect', 'aspects', 'assume', 'assumed', 'assumes', 'assuming', 'assumption', 'assumptions', 'at', 'basis', 'be', 'because', 'been', 'being', 'below', 'but', 'by', 'can', 'cause', 'caused', 'causes', 'causing', 'certain', 'comprise', 'comprised', 'comprises', 'comprising', 'could', 'currently', 'describe', 'described', 'describes', 'description', 'desired', 'detail', 'detailed', 'detailing', 'details', 'disclose', 'disclosed', 'discloses', 'disclosing', 'discuss', 'discussed', 'discussion', 'do', 'does', 'e.g', 'either', 'embodied', 'embodiment', 'embodiments', 'embody', 'etc', 'example', 'exemplary', 'fig', 'fig', 'figure', 'figure', 'figures', 'first', 'for', 'from', 'function', 'function', 'functionality', 'functioning', 'functions', 'functions', 'further', 'general', 'given', 'has', 'have', 'having', 'hereafter', 'herein', 'hereinafter', 'how', 'however', 'i.e', 'if', 'illustrate', 'illustrated', 'illustrates', 'illustration', 'implement', 'implementation', 'implemented', 'implementing', 'implements', 'in', 'include', 'include', 'included', 'includes', 'including', 'information', 'input', 'into', 'invent', 'invented', 'invention', 'inventions', 'inventors', 'invents', 'is', 'it', 'its', 'known', 'made', 'main', 'main', 'make', 'makes', 'making', 'manner', 'may', 'means', 'method', 'methods', 'might', 'must', 'noted', 'occur', 'occurred', 'occurring', 'occurs', 'of', 'on', 'one', 'or', 'ought', 'over', 'particular', 'perhaps', 'plural', 'plurality', 'possible', 'possibly', 'present', 'presently', 'prior', 'provide', 'provided', 'provides', 'providing', 'purpose', 'purposed', 'purposes', 'regard', 'relate', 'related', 'relates', 'relating', 'said', 'should', 'shown', 'similar', 'since', 'skill', 'skilled', 'so', 'some', 'step', 'steps', 'such', 'suitable', 'taught', 'teach', 'teaches', 'teaching', 'that', 'the', 'their', 'them', 'then', 'there', 'thereafter', 'thereby', 'therefore', 'therefrom', 'therein', 'thereof', 'thereon', 'these', 'they', 'third', 'this', 'those', 'though', 'through', 'thus', 'to', 'under', 'until', 'upon', 'use', 'used', 'uses', 'using', 'utilizes', 'various', 'very', 'was', 'we', 'well', 'when', 'where', 'whereby', 'wherein', 'whether', 'which', 'while', 'will', 'with', 'within', 'would', 'yet'];

const STOP_WORD_DICT = {}
STOP_WORDS.forEach(word => {
	STOP_WORD_DICT[word] = true
});

function isGeneric(word) {
	if (STOP_WORD_DICT[word]) {
		return true;
	} else {
		return false;
	}
}


module.exports = {
	isGeneric
}
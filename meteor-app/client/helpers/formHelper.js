var trimInput = function(val) {
    return val.replace(/^\s*|\s*$/g, "");
}

var isValidPassword = function(val) {
    return val.length >= 6 ? true : false; 
}

disp = function(val, type, padToLength) {
    switch(type) {
        case 'hex':
            return toHex(val, padToLength);
        case 'chr':
            return String.fromCharCode(val);
        default:
            return val; // Includes the 'dec' disp type
    }
}

var toHex = function(int_val, padToLength) {
    if (typeof padToLength != 'undefined')
        if (int_val < 0)
            return "-0x" + pad((int_val * -1).toString(), padToLength).toUpperCase();
        else
            return "0x" + pad(int_val.toString(), padToLength).toUpperCase();
    if (int_val < 0)
        return "-0x" + (int_val * -1).toString(16).toUpperCase();
    else
        return "0x" + int_val.toString(16).toUpperCase();
}

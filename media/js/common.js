function format(str) {
    for (var i = 1; i < arguments.length; i++)
        str = str.replace(new RegExp('\\{' + (i - 1) + '\\}', 'g'), arguments[i]);

    return str;
}

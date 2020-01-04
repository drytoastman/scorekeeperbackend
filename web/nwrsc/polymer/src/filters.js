export function t3(val, sign=false)
{
    // Wrapper to print floats as XXX.123 format """
    if (val === undefined) return "";
    if (typeof(val) != 'number') return val.toString();

    try {
        var ret = val.toFixed(3);
        if (sign && val >= 0) return "+"+ret;
        return ret;
    } catch (error) {
        console.log(error);
        return val.toString()
    }
}


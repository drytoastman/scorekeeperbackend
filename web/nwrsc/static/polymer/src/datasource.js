export class DataSource {

    constructor(url, callback) {
        this.ws = null;
        this.requeststr = "";
        this.url = url
        this.callback = callback;
        this.stop = false;
    }

    request(obj) {
        this.requeststr = JSON.stringify(obj)
        this._sendRequest();
    }

    shutdown() {
        this.stop = true;
        this.ws.close();
    }

    _sendRequest() {
        if (this.stop) {
            return;
        }

        if (this.ws != null && this.ws.readyState == this.ws.OPEN) {
            this.ws.send(this.requeststr);
            return;
        }

        var ws        = new WebSocket(this.url);
        ws.handler    = this;
        ws.requeststr = this.requeststr;
        ws.callback   = this.callback;
        ws.onopen     = function(e) { this.send(this.requeststr); };
        ws.onmessage  = function(e) { this.callback(JSON.parse(e.data)); };
        ws.onclose    = function(e) { console.log('wsclose'); this.handler._sendRequest(); };

        this.ws = ws;
    }
}

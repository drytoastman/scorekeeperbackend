export class DataSource {

    constructor(callback) {
        this.ws = null;
        this.requeststr = "";
        this.callback = callback;
    }

    request(obj) {
        this.requeststr = JSON.stringify(obj)
        this._sendRequest();
    }

    _sendRequest() {
        if (this.ws != null && this.ws.readyState == this.ws.OPEN) {
            this.ws.send(this.requeststr);
            return;
        }

        var ws        = new WebSocket(`ws://${window.location.hostname}/ws`);
        ws.handler    = this;
        ws.requeststr = this.requeststr;
        ws.callback   = this.callback;
        ws.onopen     = function(e) { this.send(this.requeststr); };
        ws.onmessage  = function(e) { this.callback(JSON.parse(e.data)); };
        ws.onclose    = function(e) { console.log('wsclose'); this.handler._sendRequest(); };

        this.ws = ws;
    }
}

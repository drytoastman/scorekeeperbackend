!function(t){function e(e){for(var a,l,i=e[0],c=e[1],o=e[2],p=0,h=[];p<i.length;p++)l=i[p],Object.prototype.hasOwnProperty.call(r,l)&&r[l]&&h.push(r[l][0]),r[l]=0;for(a in c)Object.prototype.hasOwnProperty.call(c,a)&&(t[a]=c[a]);for(d&&d(e);h.length;)h.shift()();return n.push.apply(n,o||[]),s()}function s(){for(var t,e=0;e<n.length;e++){for(var s=n[e],a=!0,i=1;i<s.length;i++){var c=s[i];0!==r[c]&&(a=!1)}a&&(n.splice(e--,1),t=l(l.s=s[0]))}return t}var a={},r={0:0},n=[];function l(e){if(a[e])return a[e].exports;var s=a[e]={i:e,l:!1,exports:{}};return t[e].call(s.exports,s,s.exports,l),s.l=!0,s.exports}l.m=t,l.c=a,l.d=function(t,e,s){l.o(t,e)||Object.defineProperty(t,e,{enumerable:!0,get:s})},l.r=function(t){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})},l.t=function(t,e){if(1&e&&(t=l(t)),8&e)return t;if(4&e&&"object"==typeof t&&t&&t.__esModule)return t;var s=Object.create(null);if(l.r(s),Object.defineProperty(s,"default",{enumerable:!0,value:t}),2&e&&"string"!=typeof t)for(var a in t)l.d(s,a,function(e){return t[e]}.bind(null,a));return s},l.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return l.d(e,"a",e),e},l.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},l.p="";var i=window.webpackJsonp=window.webpackJsonp||[],c=i.push.bind(i);i.push=e,i=i.slice();for(var o=0;o<i.length;o++)e(i[o]);var d=c;n.push([58,1]),s()}({11:function(t,e,s){"use strict";function a(t,e=!1){if(void 0===t)return"";if("number"!=typeof t)return t.toString();try{var s=t.toFixed(3);return e&&t>=0?"+"+s:s}catch(e){return console.log(e),t.toString()}}s.d(e,"a",(function(){return a}))},15:function(t,e,s){"use strict";s.d(e,"a",(function(){return a}));const a=s(2).b`
    table, th, td { 
        border-collapse: collapse;
        border: 1px solid var(--general-border-color);
        padding: 0 0.3rem;
        vertical-align: top; 
    }

    table {
        width: 100%;
    }

    td {
        white-space: nowrap;
    }

    td.limit {
        overflow: hidden;
        text-overflow: ellipsis;
    }

    tr.couldhave td {
        background: var(--could-have-background);
        color: var(--could-have-color);
        font-weight: bold;
        font-size: 110%;
    }

    tr.improvedon td {
        background: var(--improved-on-background);
        color: var(--improved-on-color);
        font-weight: bold;
        font-size: 110%;
    }

    tr.highlight td {
        background: var(--highlight-background);
        font-weight: bold;
        font-size: 110%;
    }

    span.change {
        font-size: 80%;
    }

    tr.head th {
        text-align: center;
        font-weight: bold;
        background-color: var(--headerfill);
        border-color: var(--headerfill);
        color: var(--headercolor);
    }
    tr.subhead th {
        text-align: center;
        font-weight: bold;
        background-color: var(--titlesfill);
        border-color: var(--titlesfill);
        color: var(--titlescolor);
    }
  `},28:function(t,e,s){"use strict";s.d(e,"a",(function(){return a}));class a{constructor(t,e){this.ws=null,this.requeststr="",this.url=t,this.callback=e,this.stop=!1}request(t){this.requeststr=JSON.stringify(t),this._sendRequest()}shutdown(){this.stop=!0,this.ws.close()}_sendRequest(){if(!this.stop)if(null==this.ws||this.ws.readyState!=this.ws.OPEN){var t=new WebSocket(this.url);t.handler=this,t.requeststr=this.requeststr,t.callback=this.callback,t.onopen=function(t){this.send(this.requeststr)},t.onmessage=function(t){this.callback(JSON.parse(t.data))},t.onclose=function(t){console.log("wsclose"),this.handler._sendRequest()},this.ws=t}else this.ws.send(this.requeststr)}}},46:function(t,e,s){"use strict";var a=s(2),r=s(11),n=s(15);class l extends a.a{static get properties(){return{entrant:{type:Object}}}static get styles(){return[n.a]}render(){if(!this.entrant)return a.c``;function t(t){return t?a.c`<span class='change'>[${Object(r.a)(t,!0)}]</span>`:""}return a.c`
        <!-- entrant -->
        <table class='res'>
        <tbody>
        <tr class='head'><th colspan='5'>${this.entrant.firstname} ${this.entrant.lastname} - Course ${this.entrant.lastcourse}</th></tr>
        <tr class='subhead'>
        <th width='10%'>#</th><th width='35%'>Raw</th><th width='10%'>C</th><th width='10%'>G</th><th width='35%'>Net</th></tr>

        ${this.entrant.runs?this.entrant.runs[this.entrant.lastcourse-1].map(e=>{return"PLC"==(s=e).status?a.c``:a.c`
        <tr>
        <tr class='${1==s.norder?"highlight":""} ${s.oldbest?"improvedon":""} ${s.ispotential?"couldhave":""}'>
        <td>${s.run}</td>
        <td>${Object(r.a)(s.raw)} ${t(s.rawimp)}</td>
        <td>${s.cones}</td>
        <td>${s.gates}</td>
        ${"OK"!=s.status?a.c`<td><span class='status'>${s.status}</td>`:a.c`<td>${Object(r.a)(s.net)} ${t(s.netimp)}</td>`}
        </tr>`;var s}):a.c``}

        </tbody>
        </table>`}}customElements.define("entrant-table",l)},52:function(t,e,s){"use strict";var a=s(2),r=s(11),n=s(15);class l extends a.a{static get properties(){return{cls:{type:Object}}}static get styles(){return[n.a]}render(){if(!this.cls)return a.c``;return a.c`
        <!-- class list -->
        <table class='res'>
        <tbody>
        <tr class='head'><th colspan='6'>Event - ${this.cls.classcode}</th></tr>
        <tr class='subhead'><th>#</th><th>Name</th><th>Idx</th><th>Net</th><th colspan='2'>Need (Raw)</th></tr>
        ${this.cls.order.map(t=>function(t){return a.c`
            <tr class='${t.current?"highlight":""} ${t.ispotential?"couldhave":""} ${t.isold?"improvedon":""}'>
            <td>${t.position}</td>
            <td class='name'>${t.firstname} ${t.lastname}</td>
            <td class='index'>${t.indexstr}</td>
            <td>${Object(r.a)(t.net)}</td>
            <td class='diffn'>${Object(r.a)(t.diffn)}</td>
            <td class='diff1'>${Object(r.a)(t.diff1)}</td>
            </tr>`}(t))}
        </tbody>
        </table>`}}customElements.define("class-table",l)},53:function(t,e,s){"use strict";var a=s(2),r=s(11),n=s(15);class l extends a.a{static get properties(){return{champ:{type:Object},display:{type:String}}}static get styles(){return[n.a]}updated(t){this.style.display=this.champ?"":"none"}render(){if(!this.champ)return a.c``;return a.c`
        <!-- class list -->
        <!-- champlist -->
        <table class='res'>
        <tbody>
        <tr class='head'><th colspan='4'>Champ - ${this.champ.classcode}</th></tr>
        <tr class='subhead'><th>#</th><th>Name</th><th></th><th>Points</th></tr>
        ${this.champ.order.map(t=>function(t){return a.c`
            <tr class='${t.current?"highlight":""} ${t.ispotential?"couldhave":""} ${t.isold?"improvedon":""}'>
            <td>${t.position}</td>
            <td>${t.firstname} ${t.lastname}</td>
            <td>${t.eventcount}</td>
            <td>${Object(r.a)(t.points.total)}</td>
            </tr>`}(t))}
        </tbody>
        </table>`}}customElements.define("champ-table",l)},54:function(t,e,s){"use strict";var a=s(2),r=s(11),n=s(15);class l extends a.a{static get properties(){return{order:{type:Object},type:{type:String}}}static get styles(){return[n.a,a.b`
            td {
                max-width: 9rem; // for the overflow to work
            }
     `]}render(){if(!this.order)return a.c``;return a.c`
        <!-- toptimes list -->
        <table class='res'>
        <tbody>
        <tr class='head'><th colspan='6'>Top Times (${this.type})</th></tr>
        <tr class='subhead'><th>#</th><th>Name</th><th>Class</th><th colspan=1>Index</th><th>Time</th></tr>
        ${this.order.map(t=>function(t){return a.c`
            <tr class='${t.current?"highlight":""} ${t.ispotential?"couldhave":""} ${t.isold?"improvedon":""}'>
            <td>${t.pos}</td>
            <td class='name limit'>${t.name}</td>
            <td>${t.classcode}</td>
            <!--<td>${t.indexstr}</td>-->
            <td>${Object(r.a)(t.indexval)}</td>
            <td>${Object(r.a)(t.time)}</td>
            </tr>`}(t))}
        </tbody>
        </table>`}}customElements.define("toptimes-table",l)},58:function(t,e,s){s(59),s(60),t.exports=s(61)},59:function(t,e,s){"use strict";s.r(e);var a=s(2),r=(s(56),s(45),s(55),s(50),s(57),s(51),s(28));s(46),s(52),s(53),s(54);class n extends a.a{static get properties(){return{prev:{type:Object},last:{type:Object},next:{type:Object},selected:{type:Number}}}static get styles(){return[a.b`
            :host {
            }

            .panel {
                display: flex;
                flex-wrap: wrap;
            }

            .panel * {
                margin: 2px;
                flex-grow: 1;
            }

            .appbar {
                display: flex;
            }

            paper-dropdown-menu {
                width: 120px;
                vertical-align: top;
                margin-top: 5px;
                --paper-input-container-color: white;
            }

            paper-listbox {
                overflow-x: hidden;
            }

            paper-tabs {
                flex-grow: 1;
                font-size: 110%;
            }
          `]}render(){return a.c`
        <div class='appbar'>
        <paper-dropdown-menu no-animations no-label-float>
            <paper-listbox slot="dropdown-content" class="dropdown-content" selected="0" @selected-changed="${this.classChange}">
              <paper-item>All</paper-item>
              ${panelConfig.classcodes.map(t=>a.c`<paper-item>${t}</paper-item>`)}
            </paper-listbox>
        </paper-dropdown-menu>

        <paper-tabs selected="1" @selected-changed="${t=>this.selected=t.target.selected}">
        <paper-tab>Prev</paper-tab>
        <paper-tab>Last</paper-tab>
        <paper-tab>Next</paper-tab>
        <paper-tab>Index</paper-tab>
        <paper-tab>Raw</paper-tab>
        </paper-tabs>
        </div>

       <iron-pages .selected="${this.selected}">
            <div class='panel'>
                <entrant-table .entrant="${this.prev?this.prev.entrant:void 0}"></entrant-table>
                <class-table       .cls="${this.prev?this.prev.class:void 0}"></class-table>
                <champ-table     .champ="${this.prev?this.prev.champ:void 0}"></champ-table>
            </div>
            <div class='panel'>
                <entrant-table .entrant="${this.last?this.last.entrant:void 0}"></entrant-table>
                <class-table       .cls="${this.last?this.last.class:void 0}"></class-table>
                <champ-table     .champ="${this.last?this.last.champ:void 0}"></champ-table>
            </div>
            <div class='panel'>
                <entrant-table .entrant="${this.next?this.next.entrant:void 0}"></entrant-table>
                <class-table       .cls="${this.next?this.next.class:void 0}"></class-table>
                <champ-table     .champ="${this.next?this.next.champ:void 0}"></champ-table>
            </div>
            <div class='panel'>
                <toptimes-table .order="${this.topnet}" type="Index"></toptimes-table>
            </div>
            <div class='panel'>
                <toptimes-table .order="${this.topraw}" type="Raw"></toptimes-table>
            </div>
        </iron-pages>
        `}classChange(t){var e=t.target.selected,s=t.target.children[e].textContent;"All"==s&&(s=null),console.log(`classchange ${s}`);var a={watch:{series:panelConfig.series,eventid:panelConfig.eventid,classcode:s,entrant:!0,class:!0,champ:!0,next:!0,topnet:!0,topraw:!0}};this.dataSource.request(a)}constructor(){super();var t=this;this.dataSource=new r.a(panelConfig.wsurl,(function(e){"last"in e&&(t.prev=t.last,t.last=e.last),"next"in e&&(t.next=e.next),"topnet"in e&&(t.topnet=e.topnet),"topraw"in e&&(t.topraw=e.topraw)}))}}customElements.define("user-panel",n)},60:function(t,e,s){"use strict";s.r(e);var a=s(2),r=(s(56),s(45),s(50),s(55),s(57),s(51),s(28)),n=(s(46),s(52),s(53),s(54),s(11)),l=s(15);class i extends a.a{static get properties(){return{order:{type:Object}}}static get styles(){return[l.a,a.b`
            td {
                max-width: 9rem; // for the overflow to work
            }
     `]}render(){if(!this.order)return a.c``;return a.c`
        <!-- next to finish table -->
        <table class='runorder'>
        <tbody>
        <tr class='head'><th colspan='6'>Next To Finish</th></tr>
        <tr class='subhead'><th>Name</th><th>Car</th><th>Class</th><th>Best</th><th>Pos</th><th>Need</th></tr>
        ${this.order.next.map(t=>function(t){return a.c`
            <tr>
            <td class='name limit'>${t.firstname} ${t.lastname}</td>
            <td class='limit'>${t.year} ${t.model} ${t.color}</td>
            <td>${t.classcode}</td>
            <td>${t.bestrun?a.c`${Object(n.a)(t.bestrun.raw)} (${t.bestrun.cones}, ${t.bestrun.gates})`:""}</td>
            <td>${t.position}</td>
            <td>${Object(n.a)(t.diffn)}</td>
            </tr>
        `}(t))}
        </tbody>
        </table>`}}customElements.define("runorder-table",i);class c extends a.a{static get properties(){return{time:{type:Number}}}static get styles(){return[l.a,a.b`
      td.timer {
        font-size: 300%;
        text-align: center;
      }
    `]}render(){return a.c`
        <!-- timer -->
        <table>
        <tbody>
        <tr class='head'><th colspan='6'>Timer</th></tr>
        <tr><td class='timer'>${this.time}</td></tr>
        </tbody>
        </table>`}}customElements.define("timer-box",c);class o extends a.a{static get properties(){return{prev:{type:Object},last:{type:Object},next:{type:Object},lastclass:{type:Object},runorder:{type:Object},timer:{type:Number},cselected:{type:Number},tselected:{type:Number}}}static get styles(){return[a.b`
            :host {
            }

            .outer {
                display: flex; 
                width: 100%;
            }

            .col1 {
                flex-grow: 1;
            }

            timer-box, runorder-table {
                display: block;
                width: 100%;
            }

            .panel {
                display: flex;
                flex-wrap: wrap;
            }

            .panel * {
                margin: 2px;
                flex-grow: 1;
            }

            .panel paper-dropdown-menu {
                flex: 100%;
                text-align: center;
            }

            paper-tabs {
                font-size: 120%;
            }
          `]}render(){return a.c`
          <!-- Main content -->
            <div class='outer'>
            <div class='col1'>
                <timer-box .time="${this.timer}"></timer-box>
                <runorder-table .order="${this.runorder}"></runorder-table>

                <div id='classtabs'>
                    <paper-tabs selected="1" @selected-changed="${t=>{this.cselected=t.target.selected}}">
                    <paper-tab>2nd Last</paper-tab>
                    <paper-tab>Last</paper-tab>
                    <paper-tab>Next</paper-tab>
                    <paper-tab>By Class</paper-tab>
                    </paper-tabs>

                    <iron-pages .selected="${this.cselected}">
                        <div>
                            <entrant-table .entrant="${this.prev?this.prev.entrant:void 0}"></entrant-table>
                            <class-table       .cls="${this.prev?this.prev.class:void 0}"></class-table>
                            <champ-table     .champ="${this.prev?this.prev.champ:void 0}"></champ-table>
                        </div>
                        <div class='panel'>
                            <entrant-table .entrant="${this.last?this.last.entrant:void 0}"></entrant-table>
                            <class-table       .cls="${this.last?this.last.class:void 0}"></class-table>
                            <champ-table     .champ="${this.last?this.last.champ:void 0}"></champ-table>
                        </div>
                        <div class='panel'>
                            <entrant-table .entrant="${this.next?this.next.entrant:void 0}"></entrant-table>
                            <class-table       .cls="${this.next?this.next.class:void 0}"></class-table>
                            <champ-table     .champ="${this.next?this.next.champ:void 0}"></champ-table>
                        </div>
                        <div class='panel'>
                            <paper-dropdown-menu no-animations no-label-float>
                            <paper-listbox slot="dropdown-content" class="dropdown-content" selected="0" @selected-changed="${this.classChange}">
                                <paper-item>Off</paper-item>
                                ${panelConfig.classcodes.map(t=>a.c`<paper-item>${t}</paper-item>`)}
                            </paper-listbox>
                            </paper-dropdown-menu>

                            <entrant-table .entrant="${this.lastclass?this.lastclass.entrant:void 0}"></entrant-table>
                            <class-table       .cls="${this.lastclass?this.lastclass.class:void 0}"></class-table>
                            <champ-table     .champ="${this.lastclass?this.lastclass.champ:void 0}"></champ-table>
                        </div>
                    </iron-pages>
                </div>
            </div>

            <div class='col2'>
                <div id='tttabs'>
                    <paper-tabs selected="0" @selected-changed="${t=>this.tselected=t.target.selected}">
                    <paper-tab>Index</paper-tab>
                    <paper-tab>Raw</paper-tab>
                    </paper-tabs>

                    <iron-pages .selected="${this.tselected}">
                        <div class='panel'>
                            <toptimes-table .order="${this.topnet}" type="Index"></toptimes-table>
                        </div>
                        <div class='panel'>
                            <toptimes-table .order="${this.topraw}" type="Raw"></toptimes-table>
                        </div>
                    </iron-pages>
                </div>
            </div>
            </div>
        `}constructor(){super();var t=this;this.classData=null,this.dataSource=new r.a(panelConfig.wsurl,(function(e){"last"in e&&(t.prev=t.last,t.last=e.last),"next"in e&&(t.next=e.next),"topnet"in e&&(t.topnet=e.topnet),"topraw"in e&&(t.topraw=e.topraw),"timer"in e&&(t.timer=e.timer),"runorder"in e&&(t.runorder=e.runorder)})),this.dataSource.request({watch:{series:panelConfig.series,eventid:panelConfig.eventid,timer:!0,runorder:!0,entrant:!0,class:!0,champ:!0,next:!0,topnet:!0,topraw:!0}})}classChange(t){var e=t.target.selected,s=t.target.children[e].textContent;if("Off"==s)return null!=this.classData&&(this.classData.shutdown(),this.classData=null),void(this.lastclass=null);var a=this;null==this.classData&&(this.classData=new r.a(panelConfig.wsurl,t=>{"last"in t&&(a.lastclass=t.last)})),this.lastclass=null,this.classData.request({watch:{series:panelConfig.series,eventid:panelConfig.eventid,classcode:s,entrant:!0,class:!0,champ:!0}})}}customElements.define("announcer-panel",o)},61:function(t,e,s){"use strict";s.r(e);var a=s(2),r=s(28),n=(s(46),s(11)),l=s(15);class i extends a.a{static get properties(){return{cls:{type:Object}}}static get styles(){return[l.a]}render(){if(!this.cls)return a.c``;return a.c`
        <!-- class list -->
        <table class='res'>
        <tbody>
        <tr class='head'><th colspan='4'>Event - ${this.cls.classcode}</th></tr>
        <tr class='subhead'><th>#</th><th>Name</th><th>Net</th><th>Diff</th></tr>
        ${this.cls.order.map(t=>function(t){return a.c`
            <tr class='${t.current?"highlight":""} ${t.ispotential?"couldhave":""} ${t.isold?"improvedon":""}'>
            <td>${t.position}</td>
            <td class='name'>${t.firstname} ${t.lastname}</td>
            <td>${Object(n.a)(t.net)}</td>
            <td class='diffn'>${Object(n.a)(t.diffn)}</td>
            </tr>`}(t))}
        </tbody>
        </table>`}}customElements.define("small-class-table",i);class c extends a.a{static get properties(){return{last:{type:Object}}}static get styles(){return[a.b`
            entrant-table, small-class-table, champ-table {
                display: block;
                font-size: 90%;
                margin-bottom: 1rem;
            }
          `]}render(){return a.c`
        <div class='panel'>
            <entrant-table .entrant="${this.last?this.last.entrant:void 0}"></entrant-table>
            <small-class-table .cls="${this.last?this.last.class:void 0}"></small-class-table>
            <champ-table     .champ="${this.last?this.last.champ:void 0}"></champ-table>
        </div>
        `}constructor(){super();var t=this;this.dataSource=new r.a(panelConfig.wsurl,(function(e){"last"in e&&(t.last=e.last)})),this.dataSource.request({watch:{series:panelConfig.series,eventid:panelConfig.eventid,entrant:!0,class:!0,champ:!0}}),document.body.style.margin="0"}}customElements.define("dataentry-panel",c)}});
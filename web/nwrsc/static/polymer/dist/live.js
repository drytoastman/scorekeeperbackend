!function(t){function e(e){for(var s,l,i=e[0],c=e[1],o=e[2],d=0,h=[];d<i.length;d++)l=i[d],Object.prototype.hasOwnProperty.call(r,l)&&r[l]&&h.push(r[l][0]),r[l]=0;for(s in c)Object.prototype.hasOwnProperty.call(c,s)&&(t[s]=c[s]);for(p&&p(e);h.length;)h.shift()();return n.push.apply(n,o||[]),a()}function a(){for(var t,e=0;e<n.length;e++){for(var a=n[e],s=!0,i=1;i<a.length;i++){var c=a[i];0!==r[c]&&(s=!1)}s&&(n.splice(e--,1),t=l(l.s=a[0]))}return t}var s={},r={0:0},n=[];function l(e){if(s[e])return s[e].exports;var a=s[e]={i:e,l:!1,exports:{}};return t[e].call(a.exports,a,a.exports,l),a.l=!0,a.exports}l.m=t,l.c=s,l.d=function(t,e,a){l.o(t,e)||Object.defineProperty(t,e,{enumerable:!0,get:a})},l.r=function(t){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})},l.t=function(t,e){if(1&e&&(t=l(t)),8&e)return t;if(4&e&&"object"==typeof t&&t&&t.__esModule)return t;var a=Object.create(null);if(l.r(a),Object.defineProperty(a,"default",{enumerable:!0,value:t}),2&e&&"string"!=typeof t)for(var s in t)l.d(a,s,function(e){return t[e]}.bind(null,s));return a},l.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return l.d(e,"a",e),e},l.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},l.p="";var i=window.webpackJsonp=window.webpackJsonp||[],c=i.push.bind(i);i.push=e,i=i.slice();for(var o=0;o<i.length;o++)e(i[o]);var p=c;n.push([59,1]),a()}({10:function(t,e,a){"use strict";function s(t,e=!1){if(void 0===t)return"";if("number"!=typeof t)return t.toString();try{var a=t.toFixed(3);return e&&t>=0?"+"+a:a}catch(e){return console.log(e),t.toString()}}a.d(e,"a",(function(){return s}))},15:function(t,e,a){"use strict";a.d(e,"a",(function(){return s}));const s=a(1).b`
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
  `},21:function(t,e,a){"use strict";a.d(e,"a",(function(){return s}));class s{constructor(t,e){this.ws=null,this.requeststr="",this.url=t,this.callback=e,this.stop=!1}request(t){this.requeststr=JSON.stringify(t),this._sendRequest()}shutdown(){this.stop=!0,this.ws.close()}_sendRequest(){if(!this.stop)if(null==this.ws||this.ws.readyState!=this.ws.OPEN){var t=new WebSocket(this.url);t.handler=this,t.requeststr=this.requeststr,t.callback=this.callback,t.onopen=function(t){this.send(this.requeststr)},t.onmessage=function(t){this.callback(JSON.parse(t.data))},t.onclose=function(t){this.handler._sendRequest()},this.ws=t}else this.ws.send(this.requeststr)}}},39:function(t,e,a){"use strict";var s=a(1),r=a(10),n=a(15);class l extends s.a{static get properties(){return{entrant:{type:Object}}}static get styles(){return[n.a]}render(){if(!this.entrant)return s.c`
            <div>Waiting for data</div>
        `;function t(t){return t?s.c`<span class='change'>[${Object(r.a)(t,!0)}]</span>`:""}return s.c`
        <!-- entrant -->
        <table class='res'>
        <tbody>
        <tr class='head'><th colspan='5'>${this.entrant.firstname} ${this.entrant.lastname} - Course ${this.entrant.lastcourse}</th></tr>
        <tr class='subhead'>
        <th width='10%'>#</th><th width='35%'>Raw</th><th width='10%'>C</th><th width='10%'>G</th><th width='35%'>Net</th></tr>

        ${this.entrant.runs?this.entrant.runs[this.entrant.lastcourse-1].map(e=>{return"PLC"==(a=e).status?s.c``:s.c`
        <tr>
        <tr class='${1==a.norder?"highlight":""} ${a.oldbest?"improvedon":""} ${a.ispotential?"couldhave":""}'>
        <td>${a.run}</td>
        <td>${Object(r.a)(a.raw)} ${t(a.rawimp)}</td>
        <td>${a.cones}</td>
        <td>${a.gates}</td>
        ${"OK"!=a.status?s.c`<td><span class='status'>${a.status}</td>`:s.c`<td>${Object(r.a)(a.net)} ${t(a.netimp)}</td>`}
        </tr>`;var a}):s.c``}

        </tbody>
        </table>`}}customElements.define("entrant-table",l)},40:function(t,e,a){"use strict";var s=a(1),r=a(10),n=a(15);class l extends s.a{static get properties(){return{cls:{type:Object},noindexcol:{type:Boolean},nodiff1col:{type:Boolean}}}static get styles(){return[n.a]}render(){if(!this.cls)return s.c``;var t=this.noindexcol,e=this.nodiff1col,a=6;return t&&a--,e&&a--,s.c`
        <!-- class list -->
        <table class='res'>
        <tbody>
        <tr class='head'><th colspan='${a}'>Event - ${this.cls.classcode}</th></tr>
        <tr class='subhead'>
        <th>#</th>
        <th>Name</th>
        ${t?"":s.c`<th>Idx</th>`}
        <th>Net</th>
        <th colspan='${e?1:2}'>Need ${e?"":"(Raw)"}</th>
        </tr>
        ${this.cls.order.map(a=>function(a){return s.c`
            <tr class='${a.current?"highlight":""} ${a.ispotential?"couldhave":""} ${a.isold?"improvedon":""}'>
            <td>${a.position}</td>
            <td class='name'>${a.firstname} ${a.lastname}</td>
            ${t?"":s.c`<td class='index'>${a.indexstr}</td>`}
            <td>${Object(r.a)(a.net)}</td>
            <td class='diffn'>${Object(r.a)(a.diffn)}</td>
            ${e?"":s.c`<td class='diff1'>${Object(r.a)(a.diff1)}</td>`}
            </tr>`}(a))}
        </tbody>
        </table>`}}customElements.define("class-table",l)},41:function(t,e,a){"use strict";var s=a(1),r=a(10),n=a(15);class l extends s.a{static get properties(){return{champ:{type:Object},display:{type:String}}}static get styles(){return[n.a]}updated(t){this.style.display=this.champ?"":"none"}render(){if(!this.champ)return s.c``;return s.c`
        <!-- class list -->
        <!-- champlist -->
        <table class='res'>
        <tbody>
        <tr class='head'><th colspan='4'>Champ - ${this.champ.classcode}</th></tr>
        <tr class='subhead'><th>#</th><th>Name</th><th></th><th>Points</th></tr>
        ${this.champ.order.map(t=>function(t){return s.c`
            <tr class='${t.current?"highlight":""} ${t.ispotential?"couldhave":""} ${t.isold?"improvedon":""}'>
            <td>${t.position}</td>
            <td>${t.firstname} ${t.lastname}</td>
            <td>${t.eventcount}</td>
            <td>${Object(r.a)(t.points.total)}</td>
            </tr>`}(t))}
        </tbody>
        </table>`}}customElements.define("champ-table",l)},51:function(t,e,a){"use strict";var s=a(1),r=a(10),n=a(15);class l extends s.a{static get properties(){return{order:{type:Object},type:{type:String}}}static get styles(){return[n.a,s.b`
            td {
                max-width: 9rem; // for the overflow to work
            }
     `]}render(){if(!this.order)return s.c``;return s.c`
        <!-- toptimes list -->
        <table class='res'>
        <tbody>
        <tr class='head'><th colspan='6'>Top Times (${this.type})</th></tr>
        <tr class='subhead'><th>#</th><th>Name</th><th>Class</th><th colspan=1>Index</th><th>Time</th></tr>
        ${this.order.map(t=>function(t){return s.c`
            <tr class='${t.current?"highlight":""} ${t.ispotential?"couldhave":""} ${t.isold?"improvedon":""}'>
            <td>${t.pos}</td>
            <td class='name limit'>${t.name}</td>
            <td>${t.classcode}</td>
            <!--<td>${t.indexstr}</td>-->
            <td>${Object(r.a)(t.indexval)}</td>
            <td>${Object(r.a)(t.time)}</td>
            </tr>`}(t))}
        </tbody>
        </table>`}}customElements.define("toptimes-table",l)},58:function(t,e,a){"use strict";var s=a(1),r=a(10),n=a(15);class l extends s.a{static get properties(){return{order:{type:Object},small:{type:Boolean}}}static get styles(){return[n.a,s.b`
            td {
                /* for overflow to work */
                max-width: 9rem;
            }
     `]}render(){if(!this.order)return s.c`
            <div>Waiting for data</div>
        `;var t=this.small;return s.c`
        <!-- next to finish table -->
        <table class='runorder'>
        <tbody>
        <tr class='head'><th colspan='${t?"5":"6"}'>Next To Finish</th></tr>
        <tr class='subhead'>
        <th>Name</th>
        ${t?"":s.c`<th>Car</th>`}
        <th>Class</th>
        <th>Best</th>
        <th>Pos</th>
        <th>Need</th>
        </tr>
        ${this.order.next.map(e=>function(e){return s.c`
            <tr>
            <td class='name limit'>${e.firstname} ${e.lastname}</td>
            ${t?"":s.c`<td class='limit'>${e.year} ${e.model} ${e.color}</td>`}
            <td>${e.classcode}</td>
            <td>${e.bestrun?s.c`${Object(r.a)(e.bestrun.raw)} (${e.bestrun.cones}, ${e.bestrun.gates})`:""}</td>
            <td>${e.position}</td>
            <td>${Object(r.a)(e.diffn)}</td>
            </tr>
        `}(e))}
        </tbody>
        </table>`}}customElements.define("runorder-table",l)},59:function(t,e,a){a(60),a(62),a(63),t.exports=a(61)},60:function(t,e,a){"use strict";a.r(e);var s=a(1),r=(a(53),a(38),a(52),a(49),a(54),a(50),a(21));a(39),a(40),a(41),a(51);class n extends s.a{static get properties(){return{prev:{type:Object},last:{type:Object},next:{type:Object},selected:{type:Number}}}static get styles(){return[s.b`
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
                max-width: 90px;
                vertical-align: top;
                margin-top: 5px;
                --paper-input-container-color: white;
            }

            paper-listbox {
                min-width: 90px;
            }

            paper-tabs {
                flex-grow: 1;
                font-size: 110%;
            }
          `]}render(){return s.c`
        <div class='appbar'>
        <paper-dropdown-menu no-animations no-label-float>
            <paper-listbox slot="dropdown-content" class="dropdown-content" selected="0" @selected-changed="${this.classChange}">
              <paper-item>All</paper-item>
              ${panelConfig.classcodes.map(t=>s.c`<paper-item>${t}</paper-item>`)}
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
        `}classChange(t){var e=t.target.selected,a=t.target.children[e].textContent;"All"==a&&(a=null),console.log(`classchange ${a}`);var s={watch:{series:panelConfig.series,eventid:panelConfig.eventid,classcode:a,entrant:!0,class:!0,champ:!0,next:!0,topnet:!0,topraw:!0}};this.dataSource.request(s)}constructor(){super();var t=this;this.dataSource=new r.a(panelConfig.wsurl,(function(e){"last"in e&&(t.prev=t.last,t.last=e.last),"next"in e&&(t.next=e.next),"topnet"in e&&(t.topnet=e.topnet),"topraw"in e&&(t.topraw=e.topraw)}))}}customElements.define("user-panel",n)},61:function(t,e,a){"use strict";a.r(e);var s=a(1),r=a(21);a(39),a(40),a(41);class n extends s.a{static get properties(){return{last:{type:Object}}}static get styles(){return[s.b`
            entrant-table, class-table, champ-table {
                display: block;
                font-size: 90%;
                margin-bottom: 1rem;
            }
          `]}render(){return s.c`
        <div class='panel'>
            <entrant-table .entrant="${this.last?this.last.entrant:void 0}"></entrant-table>
            <class-table       .cls="${this.last?this.last.class:void 0}" noindexcol=true nodiff1col=true></class-table>
            <champ-table     .champ="${this.last?this.last.champ:void 0}"></champ-table>
        </div>
        `}constructor(){super();var t=this;this.dataSource=new r.a(panelConfig.wsurl,(function(e){"last"in e&&(t.last=e.last)})),this.dataSource.request({watch:{series:panelConfig.series,eventid:panelConfig.eventid,course:panelConfig.course,entrant:!0,class:!0,champ:!0}}),document.body.style.margin="0"}}customElements.define("dataentry-panel",n)},62:function(t,e,a){"use strict";a.r(e);var s=a(1),r=(a(53),a(38),a(49),a(52),a(54),a(50),a(21)),n=(a(39),a(40),a(41),a(51),a(58),a(15)),l=a(10);class i extends s.a{static get properties(){return{time:{type:Number}}}static get styles(){return[n.a,s.b`
      td.timer {
        font-size: 300%;
        text-align: center;
      }
    `]}render(){return s.c`
        <!-- timer -->
        <table>
        <tbody>
        <tr class='head'><th colspan='6'>Timer</th></tr>
        <tr><td class='timer'>${Object(l.a)(this.time)}</td></tr>
        </tbody>
        </table>`}}customElements.define("timer-box",i);class c extends s.a{static get properties(){return{prev:{type:Object},last:{type:Object},next:{type:Object},lastclass:{type:Object},runorder:{type:Object},timer:{type:Number},cselected:{type:Number},tselected:{type:Number}}}static get styles(){return[s.b`
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

            paper-listbox {
                min-width: 100px;
            }

            paper-tabs {
                font-size: 120%;
            }
          `]}render(){return s.c`
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
                                ${panelConfig.classcodes.map(t=>s.c`<paper-item>${t}</paper-item>`)}
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
        `}constructor(){super();var t=this;this.classData=null,this.dataSource=new r.a(panelConfig.wsurl,(function(e){"last"in e&&(t.prev=t.last,t.last=e.last),"next"in e&&(t.next=e.next),"topnet"in e&&(t.topnet=e.topnet),"topraw"in e&&(t.topraw=e.topraw),"timer"in e&&(t.timer=e.timer),"runorder"in e&&(t.runorder=e.runorder)})),this.dataSource.request({watch:{series:panelConfig.series,eventid:panelConfig.eventid,timer:!0,runorder:!0,entrant:!0,class:!0,champ:!0,next:!0,topnet:!0,topraw:!0}})}classChange(t){var e=t.target.selected,a=t.target.children[e].textContent;if("Off"==a)return null!=this.classData&&(this.classData.shutdown(),this.classData=null),void(this.lastclass=null);var s=this;null==this.classData&&(this.classData=new r.a(panelConfig.wsurl,t=>{"last"in t&&(s.lastclass=t.last)})),this.lastclass=null,this.classData.request({watch:{series:panelConfig.series,eventid:panelConfig.eventid,classcode:a,entrant:!0,class:!0,champ:!0}})}}customElements.define("announcer-panel",c)},63:function(t,e,a){"use strict";a.r(e);var s=a(1),r=(a(53),a(38),a(49),a(52),a(54),a(50),a(21)),n=(a(39),a(40),a(41),a(51),a(58),a(15)),l=a(10);class i extends s.a{static get properties(){return{timedata:{type:Object}}}static get styles(){return[n.a,s.b`
      td {
        text-align: center;
        vertical-align: middle;
        height: 3rem;
        font-size: 110%;
      }
      .RL { color: red; }
      .NS { color: blue; }
      .raw { font-size: 200%; }
    `]}render(){if(!this.timedata)return s.c`
        <div>Waiting for data</div>
    `;return s.c`
        <!-- timer -->
        <table>
        <tbody>
        ${this.timedata.map(t=>{return e=t,s.c`
            <tr>
            <td class='reaction ${e.status}'>${Object(l.a)(e.reaction)}</td>
            <td class='sixty ${e.status}'>${Object(l.a)(e.sixty)}</td>
            <td class='raw ${e.status}'>${"NaN"!=e.raw?Object(l.a)(e.raw):""}</td>
            </tr>
        `;var e})}
        </tbody>
        </table>`}}customElements.define("pro-timer-box",i);class c extends s.a{static get properties(){return{leftimer:{type:Object},leftorder:{type:Object},left:{type:Object},rightimer:{type:Object},rightorder:{type:Object},right:{type:Object},lastclass:{type:Object},lastchamp:{type:Object},specclass:{type:Object},specchamp:{type:Object},hack:{type:Number},cselected:{type:Number},tselected:{type:Number}}}static get styles(){return[s.b`
            :host {
            }

            .outer {
                display: flex; 
                width: 100%;
            }

            .colcenter {
                flex-grow: 1;
            }

            pro-timer-box, runorder-table {
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

            paper-listbox {
                min-width: 100px;
            }

            paper-tabs {
                font-size: 120%;
            }

            pro-timer-box, runorder-table, entrant-table {
                display: block;
                margin-bottom: 0.5rem;
            }
          `]}render(){return s.c`
          <!-- Main content -->
            <div class='outer'>
            <div class='colleft'>
                <pro-timer-box .timedata="${this.lefttimer}"></pro-timer-box>
                <runorder-table   .order="${this.leftorder}" small="true"></runorder-table>
                <entrant-table  .entrant="${this.left}"></entrant-table>
            </div>

            <div class='colcenter'>
                <div id='classtabs'>
                    <paper-tabs selected="0" @selected-changed="${t=>{this.cselected=t.target.selected}}">
                    <paper-tab>Last</paper-tab>
                    <paper-tab>By Class</paper-tab>
                    <paper-tab>Index</paper-tab>
                    <paper-tab>Raw</paper-tab>
                    </paper-tabs>

                    <iron-pages .selected="${this.cselected}">
                        <div class='panel'>
                            <class-table       .cls="${this.lastclass}"></class-table>
                            <champ-table     .champ="${this.lastchamp}"></champ-table>
                        </div>
                        <div class='panel'>
                            <paper-dropdown-menu no-animations no-label-float>
                            <paper-listbox slot="dropdown-content" class="dropdown-content" selected="0" @selected-changed="${this.classChange}">
                                <paper-item>Off</paper-item>
                                ${panelConfig.classcodes.map(t=>s.c`<paper-item>${t}</paper-item>`)}
                            </paper-listbox>
                            </paper-dropdown-menu>

                            <class-table       .cls="${this.specclass}"></class-table>
                            <champ-table     .champ="${this.specchamp}"></champ-table>
                        </div>
                        <div class='panel'>
                                <toptimes-table .order="${this.topnet}" type="Index"></toptimes-table>
                        </div>
                        <div class='panel'>
                            <toptimes-table .order="${this.topraw}" type="Raw"></toptimes-table>
                        </div>
                    </iron-pages>
                </div>
            </div>

            <div class='colright'>
                <pro-timer-box .timedata="${this.righttimer}"></pro-timer-box>
                <runorder-table .order="${this.rightorder}" small="true"></runorder-table>
                <entrant-table .entrant="${this.right}"></entrant-table>
            </div>
            </div>
        `}constructor(){super();var t=this;this.classData=null,this.dataSource=new r.a(panelConfig.wsurl,(function(e){"last"in e&&(e.last.entrant.lastcourse>1?(t.right=e.last.entrant,t.rightorder=e.runorder):(t.left=e.last.entrant,t.leftorder=e.runorder),t.lastclass=e.last.class,t.lastchamp=e.last.champ),"topnet"in e&&(t.topnet=e.topnet),"topraw"in e&&(t.topraw=e.topraw),"protimer"in e&&(t.lefttimer=e.protimer.left,t.righttimer=e.protimer.right,t.hack=Math.random())})),this.dataSource.request({watch:{series:panelConfig.series,eventid:panelConfig.eventid,timer:!0,runorder:!0,protimer:!0,entrant:!0,class:!0,champ:!0,topnet:!0,topraw:!0}})}classChange(t){var e=t.target.selected,a=t.target.children[e].textContent;if("Off"==a)return null!=this.classData&&(this.classData.shutdown(),this.classData=null),this.specclass=null,void(this.specchamp=null);var s=this;null==this.classData&&(this.classData=new r.a(panelConfig.wsurl,t=>{"last"in t&&(s.specclass=t.last.class,s.specchamp=t.last.champ)})),this.specclass=null,this.specchamp=null,this.classData.request({watch:{series:panelConfig.series,eventid:panelConfig.eventid,classcode:a,class:!0,champ:!0}})}}customElements.define("pro-announcer-panel",c)}});
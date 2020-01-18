import { LitElement, html, css } from 'lit-element';
import { t3 } from '../filters.js';
import { tablecss } from './styles.js';

class EntrantTable extends LitElement {

  static get properties() {
    return {
      entrant: { type: Object },
    };
  }

  static get styles() {
    return [ tablecss ]
  }

  render() {
    if (!this.entrant) {
        return html`
            <div>Waiting for data</div>
        `;
    }

    function impval(val) {
        if (val) return html`<span class='change'>[${t3(val, true)}]</span>`
        return ``;
    }

    function runrow(run) {
        if (run.status == 'PLC') return html``;
        return html`
        <tr>
        <tr class='${run.norder==1 ? `highlight` : ``} ${run.oldbest ? `improvedon` : ``} ${run.ispotential ? `couldhave` : ``}'>
        <td>${run.run}</td>
        <td>${t3(run.raw)} ${impval(run.rawimp)}</td>
        <td>${run.cones}</td>
        <td>${run.gates}</td>
        ${run.status != "OK" ?  html`<td><span class='status'>${run.status}</td>` : html`<td>${t3(run.net)} ${impval(run.netimp)}</td>`}
        </tr>`;
    }

    return html`
        <!-- entrant -->
        <table class='res'>
        <tbody>
        <tr class='head'><th colspan='5'>${this.entrant.firstname} ${this.entrant.lastname} - Course ${this.entrant.lastcourse}</th></tr>
        <tr class='subhead'>
        <th width='10%'>#</th><th width='35%'>Raw</th><th width='10%'>C</th><th width='10%'>G</th><th width='35%'>Net</th></tr>

        ${this.entrant.runs ? this.entrant.runs[this.entrant.lastcourse-1].map(r => runrow(r)) : html``}

        </tbody>
        </table>`;
  }
}

customElements.define('entrant-table', EntrantTable);

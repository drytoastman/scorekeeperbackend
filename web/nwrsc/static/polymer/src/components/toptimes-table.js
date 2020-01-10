import { LitElement, html, css } from 'lit-element';
import { t3 } from '../filters.js';
import { tablecss } from './styles.js';

class TopTimesTable extends LitElement {

  static get properties() {
    return {
      order: { type: Object },
      type: { type: String },
    };
  }

  static get styles() {
    return [ tablecss, css`
            td {
                max-width: 9rem; // for the below to work
            }
            td.name {
                overflow: hidden;
                text-overflow: ellipsis;
            }
     ` ]
  }


  render() {
    if (!this.order) {
        return html``;
    }

    function erow(e) {
        return html`
            <tr class='${e.current ? 'highlight' : ''} ${e.ispotential ? 'couldhave' : ''} ${e.isold ? 'improvedon' : ''}'>
            <td>${e.pos}</td>
            <td class='name'>${e.name}</td>
            <td>${e.classcode}</td>
            <!--<td>${e.indexstr}</td>-->
            <td>${t3(e.indexval)}</td>
            <td>${t3(e.time)}</td>
            </tr>`;
    }

    return html`
        <!-- toptimes list -->
        <table class='res'>
        <tbody>
        <tr class='head'><th colspan='6'>Top Times (${this.type})</th></tr>
        <tr class='subhead'><th>#</th><th>Name</th><th>Class</th><th colspan=1>Index</th><th>Time</th></tr>
        ${this.order.map(e => erow(e))}
        </tbody>
        </table>`;
  }
}

customElements.define('toptimes-table', TopTimesTable);

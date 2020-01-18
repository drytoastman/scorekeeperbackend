import { LitElement, html, css } from 'lit-element';
import { t3 } from '../filters.js';
import { tablecss } from './styles.js';

class ClassTable extends LitElement {

  static get properties() {
    return {
      cls: { type: Object },
      noindexcol: { type: Boolean },
      nodiff1col: { type: Boolean },
    };
  }

  static get styles() {
    return [ tablecss ]
  }


  render() {
    if (!this.cls) {
        return html``;
    }

    var noindexcol = this.noindexcol;
    var nodiff1col = this.nodiff1col;
    var colspan = 6;
    if (noindexcol) colspan--;
    if (nodiff1col) colspan--;

    function erow(e) {
        return html`
            <tr class='${e.current ? 'highlight' : ''} ${e.ispotential ? 'couldhave' : ''} ${e.isold ? 'improvedon' : ''}'>
            <td>${e.position}</td>
            <td class='name'>${e.firstname} ${e.lastname}</td>
            ${noindexcol ? '' : html`<td class='index'>${e.indexstr}</td>`}
            <td>${t3(e.net)}</td>
            <td class='diffn'>${t3(e.diffn)}</td>
            ${nodiff1col ? '' : html`<td class='diff1'>${t3(e.diff1)}</td>`}
            </tr>`;
    }

    return html`
        <!-- class list -->
        <table class='res'>
        <tbody>
        <tr class='head'><th colspan='${colspan}'>Event - ${this.cls.classcode}</th></tr>
        <tr class='subhead'>
        <th>#</th>
        <th>Name</th>
        ${noindexcol ? '' : html`<th>Idx</th>`}
        <th>Net</th>
        <th colspan='${nodiff1col ? 1 : 2}'>Need ${nodiff1col ? '' : '(Raw)'}</th>
        </tr>
        ${this.cls.order.map(e => erow(e))}
        </tbody>
        </table>`;
  }
}

customElements.define('class-table', ClassTable);

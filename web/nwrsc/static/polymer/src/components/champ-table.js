import { LitElement, html, css } from 'lit-element';
import { t3 } from '../filters.js';
import { tablecss } from './styles.js';

class ChampTable extends LitElement {

  static get properties() {
    return {
      champ: { type: Object },
      display: { type: String }
    };
  }

  static get styles() {
    return [ tablecss ]
  }

  updated(changed) {
    this.style.display = this.champ ? "" : "none";
  }

  render() {
    if (!this.champ) {
        return html``;
    }

    function erow(e) {
        return html`
            <tr class='${e.current ? 'highlight' : ''} ${e.ispotential ? 'couldhave' : ''} ${e.isold ? 'improvedon' : ''}'>
            <td>${e.position}</td>
            <td>${e.firstname} ${e.lastname}</td>
            <td>${e.eventcount}</td>
            <td>${t3(e.points.total)}</td>
            </tr>`;
    }

    return html`
        <!-- class list -->
        <!-- champlist -->
        <table class='res'>
        <tbody>
        <tr class='head'><th colspan='4'>Champ - ${this.champ.classcode}</th></tr>
        <tr class='subhead'><th>#</th><th>Name</th><th></th><th>Points</th></tr>
        ${this.champ.order.map(e => erow(e))}
        </tbody>
        </table>`;
  }
}

customElements.define('champ-table', ChampTable);

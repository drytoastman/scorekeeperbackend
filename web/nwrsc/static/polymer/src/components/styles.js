import { css } from 'lit-element';

export const tablecss = css`
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
  `;

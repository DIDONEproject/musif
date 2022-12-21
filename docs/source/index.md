# Welcome to musiF's documentation!

```{toctree}
---
maxdepth: 2
hidden:
---

Getting Started <Tutorial>
Configuration
Custom_features
Caching
API <API/modules>
General Index <genindex>
Module Index <modindex>
Search <search>
```

`musiF` is a Python module for computing features from music scores. It is especially
designed for arias from 18th Century Italian Operas. It has extensively been used and
designed by the [Didone](https://didone.eu) team for analyzing Opera arias from the
Metastasian literature.

Please, see the [Tutorial](Tutorial.html) for an easy introduction.

For more advanced usage, have a look at the [Configuration](Configuration.html),
[Custom Features](Custom_features.html), and [Caching](Caching.html) pages.

If you have any issue or question, feel free to open an issue on our [Github
repo](https://github.com/DIDONEproject/musiF/).

## Build docs by hand
* `pipx install sphinx`
* `pipx inject sphinx myst_nb`
* `make html`

<p style="text-align:center;margin:100px 0;">
  <a href="https://www.ucm.es" target="_blank"><img src="./_static/imgs/ucm.jpg" alt="Logo UCM" align="middle"></a>
  <a href="https://iccmu.es/" target="_blank"> <img src="./_static/imgs/iccmu.png" alt="Logo ICCMU" align="middle"></a>
  <a href="https://www.uc3m.es" target="_blank"><img src="./_static/imgs/uc3m.png" alt="Logo UC3M" align="middle"></a>
  <a href="https://erc.europa.eu/" target="_blank"><img src="./_static/imgs/erc.jpg" alt="Logo DIDONE ERC" align="middle"></a>
</p>


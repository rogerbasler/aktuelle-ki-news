"""Impressum und Datenschutz in DE, EN, ES (HTML-Fragmente)."""

OWNER = {
    "name": "Roger Basler de Roca",
    "company": "Analytics Agentur",
    "street": "The Circle 6",
    "city": "8058 Zürich",
    "country": {"de": "Schweiz", "en": "Switzerland", "es": "Suiza"},
    "email": "mail@rogerbasler.ch",
    "web": "https://fragroger.ai",
}

IMPRINT = {
    "de": """
<h2>Verantwortlich für den Inhalt</h2>
<p>{name}<br>{company}<br>{street}<br>{city}<br>{country}</p>
<p>E-Mail: <a href="mailto:{email}">{email}</a><br>Web: <a href="{web}">{web}</a></p>
<h2>Was diese Seite ist</h2>
<p>KI Power Update ist ein wöchentlicher, redaktionell kuratierter Überblick über KI-Meldungen aus t3n, heise, Handelsblatt und TechCrunch. Die Seite erscheint jeden Samstag und wird in Partnerschaft mit <a href="https://ki-power.me" rel="noopener">ki-power.me</a> betrieben.</p>
<h2>Haftungsausschluss</h2>
<p>Die Inhalte werden mit Sorgfalt erstellt, Auswahl, Zusammenfassungen, Übersetzungen und die Podcast-Stimme entstehen jedoch mit Unterstützung von KI-Systemen und werden automatisiert veröffentlicht. Für Richtigkeit, Vollständigkeit und Aktualität wird keine Gewähr übernommen. Haftungsansprüche wegen Schäden materieller oder immaterieller Art, die aus der Nutzung oder Nichtnutzung der Informationen entstehen, sind ausgeschlossen, soweit gesetzlich zulässig. Die Inhalte stellen keine Anlage-, Rechts- oder sonstige Beratung dar.</p>
<h2>Links auf Drittseiten</h2>
<p>Jede Meldung verlinkt auf den Originalartikel des jeweiligen Verlags. Für Inhalte verlinkter Seiten sind ausschliesslich deren Betreiber verantwortlich. Die Zusammenfassungen geben den Inhalt der Originalartikel in eigenen Worten wieder; alle Rechte an den Originaltexten liegen bei den Verlagen.</p>
<h2>Urheberrecht</h2>
<p>Die auf dieser Seite erstellten Zusammenfassungen, Skripte und Audiodateien dürfen mit Quellenangabe ("KI Power Update, news.fragroger.ai") geteilt werden. Markennamen und Logos Dritter gehören den jeweiligen Inhaber:innen.</p>
""",
    "en": """
<h2>Responsible for the content</h2>
<p>{name}<br>{company}<br>{street}<br>{city}<br>{country}</p>
<p>Email: <a href="mailto:{email}">{email}</a><br>Web: <a href="{web}">{web}</a></p>
<h2>What this site is</h2>
<p>KI Power Update is a weekly, editorially curated overview of AI news from t3n, heise, Handelsblatt and TechCrunch. It is published every Saturday and operated in partnership with <a href="https://ki-power.me" rel="noopener">ki-power.me</a>.</p>
<h2>Disclaimer</h2>
<p>The content is prepared with care; however, selection, summaries, translations and the podcast voice are produced with the help of AI systems and published automatically. No guarantee is given for accuracy, completeness or timeliness. Liability claims for material or immaterial damage arising from the use or non-use of the information are excluded to the extent permitted by law. The content does not constitute investment, legal or other advice.</p>
<h2>Links to third-party sites</h2>
<p>Each story links to the original article of the respective publisher. The operators of linked pages are solely responsible for their content. The summaries restate the original articles in our own words; all rights to the original texts remain with the publishers.</p>
<h2>Copyright</h2>
<p>Summaries, scripts and audio files created on this site may be shared with attribution ("KI Power Update, news.fragroger.ai"). Third-party brand names and logos belong to their respective owners.</p>
""",
    "es": """
<h2>Responsable del contenido</h2>
<p>{name}<br>{company}<br>{street}<br>{city}<br>{country}</p>
<p>Correo: <a href="mailto:{email}">{email}</a><br>Web: <a href="{web}">{web}</a></p>
<h2>Qué es este sitio</h2>
<p>KI Power Update es un resumen semanal, curado editorialmente, de noticias sobre IA de t3n, heise, Handelsblatt y TechCrunch. Se publica cada sábado y se gestiona en colaboración con <a href="https://ki-power.me" rel="noopener">ki-power.me</a>.</p>
<h2>Exención de responsabilidad</h2>
<p>Los contenidos se elaboran con cuidado; sin embargo, la selección, los resúmenes, las traducciones y la voz del pódcast se producen con ayuda de sistemas de IA y se publican de forma automatizada. No se garantiza su exactitud, integridad ni actualidad. Quedan excluidas, en la medida permitida por la ley, las reclamaciones de responsabilidad por daños materiales o inmateriales derivados del uso o no uso de la información. Los contenidos no constituyen asesoramiento financiero, legal ni de otro tipo.</p>
<h2>Enlaces a terceros</h2>
<p>Cada noticia enlaza al artículo original de la editorial correspondiente. Los operadores de las páginas enlazadas son los únicos responsables de sus contenidos. Los resúmenes reproducen los artículos originales con palabras propias; todos los derechos sobre los textos originales pertenecen a las editoriales.</p>
<h2>Derechos de autor</h2>
<p>Los resúmenes, guiones y archivos de audio creados en este sitio pueden compartirse citando la fuente ("KI Power Update, news.fragroger.ai"). Las marcas y logotipos de terceros pertenecen a sus respectivos titulares.</p>
""",
}

PRIVACY = {
    "de": """
<p>Diese Seite kommt ohne Cookies, ohne Tracking und ohne externe Schriftarten oder Skripte von Drittanbietern aus. Es werden keine Nutzerkonten geführt und keine Formulare angeboten.</p>
<h2>Verantwortliche Stelle</h2>
<p>{name}, {company}, {street}, {city}, {country}, <a href="mailto:{email}">{email}</a></p>
<h2>Hosting</h2>
<p>Die Seite wird über GitHub Pages (GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, USA) ausgeliefert. Beim Aufruf verarbeitet GitHub technisch notwendige Verbindungsdaten wie IP-Adresse, Zeitpunkt des Zugriffs, aufgerufene Seite, Browsertyp und Referrer in Server-Logs, um die Seite bereitzustellen und die Sicherheit des Dienstes zu gewährleisten. Rechtsgrundlage ist das berechtigte Interesse am sicheren Betrieb der Website. Details: <a href="https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener">GitHub Privacy Statement</a>.</p>
<h2>Audio und Suche</h2>
<p>Podcast-Dateien und der Suchindex werden vom selben Host geladen. Die Suche läuft vollständig im Browser; Suchbegriffe werden nicht übertragen oder gespeichert.</p>
<h2>Externe Links</h2>
<p>Beim Klick auf einen Originalartikel gelten die Datenschutzbestimmungen des jeweiligen Verlags (t3n, heise, Handelsblatt, TechCrunch) sowie von ki-power.me und fragroger.ai.</p>
<h2>Ihre Rechte</h2>
<p>Sie haben nach dem Schweizer Datenschutzgesetz (DSG) und, soweit anwendbar, der DSGVO das Recht auf Auskunft, Berichtigung, Löschung und Einschränkung der Bearbeitung Ihrer Personendaten. Wenden Sie sich dazu an <a href="mailto:{email}">{email}</a>.</p>
<p>Stand: Oktober 2026</p>
""",
    "en": """
<p>This site uses no cookies, no tracking and no external fonts or third-party scripts. There are no user accounts and no forms.</p>
<h2>Controller</h2>
<p>{name}, {company}, {street}, {city}, {country}, <a href="mailto:{email}">{email}</a></p>
<h2>Hosting</h2>
<p>The site is delivered via GitHub Pages (GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, USA). When you visit, GitHub processes technically necessary connection data such as IP address, time of access, page requested, browser type and referrer in server logs in order to deliver the site and ensure the security of the service. The legal basis is the legitimate interest in operating the website securely. Details: <a href="https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener">GitHub Privacy Statement</a>.</p>
<h2>Audio and search</h2>
<p>Podcast files and the search index are loaded from the same host. The search runs entirely in your browser; search terms are neither transmitted nor stored.</p>
<h2>External links</h2>
<p>When you open an original article, the privacy policies of the respective publisher (t3n, heise, Handelsblatt, TechCrunch) as well as of ki-power.me and fragroger.ai apply.</p>
<h2>Your rights</h2>
<p>Under the Swiss Data Protection Act (FADP) and, where applicable, the GDPR, you have the right to access, rectify, erase and restrict the processing of your personal data. Please contact <a href="mailto:{email}">{email}</a>.</p>
<p>Last updated: October 2026</p>
""",
    "es": """
<p>Este sitio no utiliza cookies, ni rastreo, ni fuentes externas ni scripts de terceros. No hay cuentas de usuario ni formularios.</p>
<h2>Responsable</h2>
<p>{name}, {company}, {street}, {city}, {country}, <a href="mailto:{email}">{email}</a></p>
<h2>Alojamiento</h2>
<p>El sitio se sirve a través de GitHub Pages (GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, EE. UU.). Al visitarlo, GitHub procesa en sus registros de servidor datos de conexión técnicamente necesarios, como la dirección IP, la hora de acceso, la página solicitada, el tipo de navegador y el referente, para entregar el sitio y garantizar la seguridad del servicio. La base jurídica es el interés legítimo en el funcionamiento seguro del sitio. Detalles: <a href="https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener">GitHub Privacy Statement</a>.</p>
<h2>Audio y búsqueda</h2>
<p>Los archivos del pódcast y el índice de búsqueda se cargan desde el mismo servidor. La búsqueda se ejecuta íntegramente en el navegador; los términos de búsqueda no se transmiten ni se almacenan.</p>
<h2>Enlaces externos</h2>
<p>Al abrir un artículo original se aplican las políticas de privacidad de la editorial correspondiente (t3n, heise, Handelsblatt, TechCrunch), así como las de ki-power.me y fragroger.ai.</p>
<h2>Sus derechos</h2>
<p>Conforme a la Ley suiza de Protección de Datos (LPD) y, cuando proceda, al RGPD, tiene derecho a acceder, rectificar, suprimir y limitar el tratamiento de sus datos personales. Escriba a <a href="mailto:{email}">{email}</a>.</p>
<p>Última actualización: octubre de 2026</p>
""",
}


def render(kind, lang):
    tpl = (IMPRINT if kind == "imprint" else PRIVACY)[lang]
    vals = dict(OWNER)
    vals["country"] = OWNER["country"][lang]
    return tpl.format(**vals)

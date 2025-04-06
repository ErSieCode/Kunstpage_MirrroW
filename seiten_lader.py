# -*- coding: utf-8 -*- # Sicherstellen, dass Umlaute im Code ok sind
import time
import json
import os
import logging
from urllib.parse import urljoin, urlparse, unquote
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from requests.exceptions import RequestException
import re

# --- Konfiguration ---
START_URLS = [
    "https://karl-ulinger.blogspot.com/",
    "https://karl-ulinger.blogspot.com/p/werke.html",
    # Die anderen spezifischen URLs sind gut, werden aber sowieso vom Crawler gefunden, wenn sie verlinkt sind.
    # Man kann sie drin lassen, schadet nicht.
    "https://karl-ulinger.blogspot.com/2018/11/jipie-hura-das-passwort-ist-wieder-da.html",
    "https://karl-ulinger.blogspot.com/p/groformat-70-x-150cm.html",
    "https://karl-ulinger.blogspot.com/p/news.html",
    "https://karl-ulinger.blogspot.com/2014/01/karl-ulinger-ist-auf-die-nudel-gekommen.html?m=1"
]
OUTPUT_JSON_FILE = 'karl_ulinger_werke_final.json'
MAX_PAGES_TO_VISIT = 300 # Deutlich erhöht für gründlicheres Crawling
REQUEST_DELAY = 0.7 # Etwas aggressiver, aber noch vertretbar
REQUEST_TIMEOUT = 30 # Längerer Timeout für langsamere Seiten
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36', # Neuerer Agent
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://www.google.com/' # Referer hinzufügen kann manchmal helfen
}

# Logging einrichten
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Optional: Debug-Level für BeautifulSoup und Requests reduzieren, da sie sehr gesprächig sein können
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("chardet").setLevel(logging.WARNING)


# --- Hilfsfunktionen ---

def get_page_content_requests(url):
    """Lädt eine Seite mit requests und gibt den HTML-Inhalt zurück."""
    try:
        logging.info(f"Lade Seite: {url}")
        session = requests.Session() # Verwende eine Session
        response = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, verify=True) # verify=True ist Standard, aber explizit
        response.raise_for_status()
        # Wähle Encoding sorgfältig
        if response.encoding is None or response.encoding == 'ISO-8859-1':
             # Wenn requests unsicher ist oder ISO rät, versuche UTF-8 oder apparent_encoding
             response.encoding = response.apparent_encoding if response.apparent_encoding else 'utf-8'
        logging.debug(f"Verwendetes Encoding für {url}: {response.encoding}")
        return response.text
    except RequestException as e:
        logging.error(f"Fehler beim Laden von {url} mit requests: {e}")
        return None
    except Exception as e:
        logging.error(f"Unerwarteter Fehler beim Laden von {url}: {e}")
        return None

def clean_text(text):
    """Bereinigt Text von überflüssigen Leerzeichen und Zeilenumbrüchen."""
    if not text or not isinstance(text, str):
        return None
    try:
        # Ersetzt mehrere Leerzeichen/Umbruch durch einzelnes Leerzeichen
        text = re.sub(r'\s+', ' ', text, flags=re.UNICODE)
        return text.strip()
    except Exception as e:
        logging.warning(f"Fehler bei Textbereinigung: {e} - Text: {text[:100]}...")
        return text # Gib Original zurück im Fehlerfall

def extract_title_from_filename(image_url):
    """Versucht, einen Titel aus dem Dateinamen der Bild-URL abzuleiten."""
    if not image_url: return None
    try:
        path = urlparse(image_url).path
        filename = os.path.basename(unquote(path)) # Dekodiert %20 etc.
        name_part, _ = os.path.splitext(filename)
        # Ersetze gängige Trennzeichen durch Leerzeichen
        title = re.sub(r'[+_-]', ' ', name_part)
        # Entferne mögliche Reste wie sXXX, wXXX etc. am Ende
        title = re.sub(r'\s+[swh]\d+([-a-z]+)?$', '', title, flags=re.IGNORECASE).strip()
        # Entferne Zahlen am Anfang oder Ende, die wie IDs aussehen (optional, kann Titel ändern)
        # title = re.sub(r'^\d+\s|\s+\d+$', '', title).strip()
        # Großschreibung am Anfang jedes Wortes? Geschmackssache.
        # return title.title() if title else None
        return title if title else None
    except Exception as e:
        logging.debug(f"Fehler beim Extrahieren des Titels aus Dateiname {image_url}: {e}")
        return None

def get_relevant_text_elements(start_node, max_distance=3, stop_tags=['div','table','ul','ol']):
    """Sammelt Text-Nodes und einfache Tags (wie b, i, span) um einen Start-Node."""
    elements = []
    # Rückwärts
    node = start_node.find_previous_sibling()
    count = 0
    while node and count < max_distance:
        if isinstance(node, Tag):
            if node.name in stop_tags: break # Stoppe bei großen blockierenden Tags
            if node.name == 'br': # Überspringe <br>
                 node = node.find_previous_sibling()
                 continue
            elements.insert(0, node) # Füge das Tag selbst hinzu
            count += 1
        elif isinstance(node, NavigableString):
            if clean_text(str(node)): # Nur wenn es nicht leer ist
                elements.insert(0, node)
                count += 1
        node = node.find_previous_sibling()

    # Vorwärts
    node = start_node.find_next_sibling()
    count = 0
    while node and count < max_distance:
        if isinstance(node, Tag):
            if node.name in stop_tags: break
            # Ignoriere direkt folgende Bild-Separators
            if node.name == 'div' and 'separator' in node.get('class', []):
                node = node.find_next_sibling()
                continue
            if node.name == 'br':
                 node = node.find_next_sibling()
                 continue
            elements.append(node)
            count += 1
        elif isinstance(node, NavigableString):
             if clean_text(str(node)):
                 elements.append(node)
                 count += 1
        node = node.find_next_sibling()
    return elements

def extract_artwork_data(soup, url):
    """Fokussiert auf Bilder, extrahiert Kontext und versucht Titel/Datum/Beschreibung zuzuordnen."""
    artworks = []
    processed_image_urls = set()

    # Finde alle Posts/Seiteninhalte
    content_containers = soup.find_all('div', class_=re.compile(r'post-outer|post hentry|post-body|entry-content'))
    if not content_containers:
        main_content = soup.find('main') or soup.find('div', id=re.compile(r'main|content|page')) or soup.body
        if main_content: content_containers = [main_content]
        else: content_containers = [soup.body] # Fallback

    for post_index, container in enumerate(content_containers):
        # --- Basisinformationen des Containers (Post/Seite) ---
        post_title = None
        post_date = None
        try:
            # Versuche Post-Titel zu finden (kann auch Seitentitel sein)
            title_tag = container.find(['h1','h2','h3'], class_=re.compile(r'post-title|entry-title'))
            if not title_tag and post_index == 0: # Für den ersten Container auch Seitentitel prüfen
                 title_tag = soup.find('head').find('title')
            post_title = clean_text(title_tag.get_text()) if title_tag else f"Unbenannter Container {post_index+1}"

            # Versuche Post-/Seiten-Datum zu finden (Robustere Prüfung)
            date_tag = container.find(class_=re.compile(r'date-header|published|timestamp')) or container.find('time')
            if date_tag:
                date_text = clean_text(date_tag.get_text())
                # Sicherer Zugriff auf 'datetime' Attribut
                datetime_attr = date_tag.get('datetime')
                title_attr = date_tag.get('title') # Manchmal im 'title' Attribut
                if datetime_attr:
                     post_date = datetime_attr # Bevorzuge datetime Attribut
                elif date_text:
                     post_date = date_text
                elif title_attr:
                     post_date = title_attr # Fallback auf title Attribut
        except Exception as e:
            logging.warning(f"Fehler beim Extrahieren von Post-Metadaten: {e}")
            if not post_title: post_title = f"Unbenannter Container {post_index+1}"

        # --- Finde alle Bilder (innerhalb von Links bevorzugt) ---
        # Priorität 1: Bilder in div.separator > a > img
        image_links_in_separators = container.select('div.separator a > img')
        # Priorität 2: Bilder in Links generell (a > img), die NICHT in sep. sind
        image_links_general = [img for img in container.select('a > img') if not img.find_parent('div', class_='separator')]
        # Priorität 3: Bilder ohne Links (img)
        # direct_images = [img for img in container.find_all('img', src=True) if not img.find_parent('a')]
        # Wir konzentrieren uns erstmal auf Bilder mit Links, da diese meist die "Werke" sind.

        all_image_tags = image_links_in_separators + image_links_general
        logging.debug(f"Container '{post_title}': Gefundene verlinkte Bilder: {len(all_image_tags)}")

        for img_tag in all_image_tags:
            artwork_info = {
                "Name des Werkes": None, "Erscheinungsdatum": None, "Kunstform": None,
                "Formatgröße": None, "Beschreibung des Bildes": None,
                "Thumpnail des Bildes als link": None, "Das ganze Bild als vollen roh link": None,
                "Quell_URL": url, "Ursprungs_Post_Titel": post_title, "Ursprungs_Post_Datum": post_date
            }
            try:
                # --- Bild-Links extrahieren ---
                thumb_url_raw = img_tag.get('src')
                # Finde den übergeordneten Link-Tag
                img_link_tag = img_tag.find_parent('a', href=True)
                if not img_link_tag: continue # Sollte nicht passieren bei select('a > img'), aber sicher ist sicher

                full_url_raw = img_link_tag.get('href')
                if not thumb_url_raw or not full_url_raw: continue

                artwork_info["Thumpnail des Bildes als link"] = urljoin(url, thumb_url_raw)
                full_url_absolute = urljoin(url, full_url_raw)

                # Duplikatprüfung
                if full_url_absolute in processed_image_urls: continue
                processed_image_urls.add(full_url_absolute)

                # "Rohe" URL extrahieren
                original_raw_url = full_url_absolute
                raw_url = re.sub(r'/[swh]\d+(-[a-z0-9]+)?/', '/s0/', full_url_absolute) # s0 für Original
                if raw_url == original_raw_url: # Wenn /s0/ nicht klappte, versuche nur Pfadteil zu entfernen
                     parts = full_url_absolute.split('/')
                     if len(parts) > 1 and re.match(r'^[swh]\d+', parts[-2], re.IGNORECASE):
                         raw_url = '/'.join(parts[:-2] + [parts[-1]])
                artwork_info["Das ganze Bild als vollen roh link"] = raw_url
                if raw_url != original_raw_url:
                     logging.debug(f"Bild-URL bereinigt: {original_raw_url} -> {raw_url}")
                else:
                     logging.debug(f"Bild-URL nicht bereinigt (kein Muster gefunden): {original_raw_url}")


                # --- Kontext finden ---
                # Finde den "wichtigsten" Container um das Bild (oft div.separator oder der Link selbst)
                context_node = img_tag.find_parent('div', class_='separator') or img_link_tag

                # Sammle Text-Elemente und einfache Tags um den Kontext-Node
                relevant_elements = get_relevant_text_elements(context_node, max_distance=3)
                surrounding_text = " ".join(clean_text(el.get_text()) for el in relevant_elements if el.get_text).strip()


                # --- Titel extrahieren ---
                title_found = False
                # 1. Prüfe Elemente direkt davor/danach auf Fett/Überschrift
                for element in relevant_elements:
                     if element.name in ['b', 'strong', 'h4', 'h5', 'h6']:
                         potential_title = clean_text(element.get_text())
                         if potential_title:
                             artwork_info["Name des Werkes"] = potential_title
                             title_found = True
                             logging.debug(f"Titel (Formatierung): {artwork_info['Name des Werkes']}")
                             break # Nimm den ersten Treffer
                # 2. Alt-Text
                if not title_found and img_tag.get('alt'):
                     alt_text = clean_text(img_tag['alt'])
                     # Ignoriere generische Alt-Texte
                     if alt_text and len(alt_text) > 3 and not alt_text.lower().startswith(('http', 'bild', 'image')):
                         artwork_info["Name des Werkes"] = alt_text
                         title_found = True
                         logging.debug(f"Titel (Alt-Text): {artwork_info['Name des Werkes']}")
                # 3. Dateiname
                if not title_found:
                    title_from_file = extract_title_from_filename(full_url_absolute)
                    if title_from_file:
                        artwork_info["Name des Werkes"] = title_from_file
                        title_found = True
                        logging.debug(f"Titel (Dateiname): {artwork_info['Name des Werkes']}")
                # 4. Kurzer Text aus Umgebung (heuristisch)
                if not title_found and surrounding_text:
                     potential_title = surrounding_text.split('.')[0].split('\n')[0].strip()
                     if 2 < len(potential_title) < 70 and not potential_title.endswith(('.',':','?','!')):
                         # Vergleiche mit Post-Titel, um Redundanz zu vermeiden
                         if not post_title or potential_title.lower() not in post_title.lower():
                              artwork_info["Name des Werkes"] = potential_title
                              title_found = True
                              logging.debug(f"Titel (Umgebungstext): {artwork_info['Name des Werkes']}")
                # 5. Fallback: Post-Titel mit Index?
                if not title_found:
                    image_index_in_post = all_image_tags.index(img_tag) + 1
                    artwork_info["Name des Werkes"] = f"Bild {image_index_in_post} aus: {post_title}"
                    logging.debug(f"Titel (Fallback Post-Titel + Index): {artwork_info['Name des Werkes']}")

                # --- Datum extrahieren ---
                date_found = False
                # 1. Suche (YYYY) im Text um das Bild
                combined_text_for_date = surrounding_text + " " + clean_text(context_node.get_text()) # Auch Text im Separator prüfen
                if combined_text_for_date:
                    date_match = re.search(r'\((20\d{2}|19\d{2})\)', combined_text_for_date) # Suche (19xx) oder (20xx)
                    if date_match:
                        artwork_info["Erscheinungsdatum"] = date_match.group(1)
                        date_found = True
                        logging.debug(f"Datum (YYYY aus Kontext): {artwork_info['Erscheinungsdatum']}")
                # 2. Fallback: Post-Datum
                if not date_found and post_date:
                    # Versuche nur das Jahr aus dem Post-Datum zu extrahieren, wenn möglich
                    year_match = re.search(r'(20\d{2}|19\d{2})', str(post_date))
                    if year_match:
                         artwork_info["Erscheinungsdatum"] = year_match.group(1)
                    else:
                         artwork_info["Erscheinungsdatum"] = str(post_date) # Nimm das volle Datum als Fallback
                    logging.debug(f"Datum (Fallback Post-Datum): {artwork_info['Erscheinungsdatum']}")

                # --- Beschreibung extrahieren ---
                # Nimm allen Text aus den relevanten Elementen, entferne Titel/Datum falls gefunden
                full_description = surrounding_text
                # Füge Text aus dem Separator/Link hinzu, der nicht der Linktext/Alt-Text ist
                context_texts = context_node.find_all(string=True, recursive=False) # Nur direkte Kinder
                link_text_raw = clean_text(img_link_tag.get_text())
                alt_text_raw = clean_text(img_tag.get('alt',""))
                for ct in context_texts:
                     ct_clean = clean_text(str(ct))
                     if ct_clean and ct_clean != link_text_raw and ct_clean != alt_text_raw:
                          # Ignoriere, wenn es das gefundene Datum ist
                          if not (date_found and artwork_info["Erscheinungsdatum"] and f"({artwork_info['Erscheinungsdatum']})" == ct_clean):
                               full_description += " " + ct_clean

                full_description = clean_text(full_description)
                # Entferne Titel/Datum aus Beschreibung
                if title_found and artwork_info["Name des Werkes"] and artwork_info["Name des Werkes"] in full_description:
                    full_description = full_description.replace(artwork_info["Name des Werkes"], "", 1)
                if date_found and artwork_info["Erscheinungsdatum"] and f"({artwork_info['Erscheinungsdatum']})" in full_description:
                    full_description = full_description.replace(f"({artwork_info['Erscheinungsdatum']})", "", 1)

                artwork_info["Beschreibung des Bildes"] = clean_text(full_description)


                # --- Kunstform / Größe extrahieren (Heuristisch) ---
                if artwork_info["Beschreibung des Bildes"]:
                    desc_lower = artwork_info["Beschreibung des Bildes"].lower()
                    kunstform_parts = []
                    if "acryl" in desc_lower: kunstform_parts.append("Acryl")
                    if "öl" in desc_lower or "oel" in desc_lower: kunstform_parts.append("Öl")
                    # Reihenfolge beachten: "auf Leinwand" etc.
                    if "leinwand" in desc_lower or "canvas" in desc_lower: kunstform_parts.append("auf Leinwand")
                    elif "papier" in desc_lower: kunstform_parts.append("auf Papier")
                    elif "karton" in desc_lower: kunstform_parts.append("auf Karton")
                    elif "holz" in desc_lower: kunstform_parts.append("auf Holz")

                    # Nur hinzufügen, wenn etwas gefunden wurde
                    if kunstform_parts:
                         # Vermeide Duplikate wie "Acryl auf Leinwand auf Leinwand"
                         if len(kunstform_parts) > 1 and kunstform_parts[-1].startswith("auf") and kunstform_parts[-2].startswith("auf"):
                              kunstform_parts.pop(-2) # Entferne das vorletzte "auf X"
                         artwork_info["Kunstform"] = " ".join(kunstform_parts)


                    # Größe
                    # Suche nach "100 x 100 cm", "100x100cm", "ca. 100 x 100", "Format: 100x100"
                    size_match = re.search(r'(\d+)\s*[xX\*]\s*(\d+)\s*(cm)?', artwork_info["Beschreibung des Bildes"])
                    if size_match:
                        size_str = f"{size_match.group(1)}x{size_match.group(2)}"
                        if size_match.group(3) or 'cm' in desc_lower: # Wenn cm dabei steht oder im Text vorkommt
                            size_str += "cm"
                        artwork_info["Formatgröße"] = size_str

                # --- Werk hinzufügen ---
                if artwork_info["Das ganze Bild als vollen roh link"]:
                    logging.info(f"--> Extrahiert: '{artwork_info['Name des Werkes']}' ({artwork_info['Erscheinungsdatum']})")
                    artworks.append(artwork_info)

            except Exception as e_img:
                logging.warning(f"Fehler bei Verarbeitung eines Bildes in '{post_title}' (URL: {url}): {e_img}", exc_info=False) # Nicht den ganzen Traceback loggen

    return artworks

def find_internal_links(soup, base_url):
    """Findet interne Links, inkl. Blogspot-Paginierung."""
    internal_links = set()
    try:
        base_domain = urlparse(base_url).netloc
    except ValueError:
        return internal_links

    for link in soup.find_all('a', href=True):
        href = link['href']
        if not href or href.startswith(('#', 'javascript:', 'mailto:')):
            continue

        try:
            absolute_url = urljoin(base_url, href)
            parsed_url = urlparse(absolute_url)

            if parsed_url.scheme in ['http', 'https'] and parsed_url.netloc == base_domain:
                clean_url = parsed_url._replace(fragment="").geturl()

                # Ignoriere bekannte irrelevante Muster
                if any(clean_url.lower().endswith(ext) for ext in [
                    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.pdf', '.zip',
                    '.rar', '.css', '.js', '.xml', '/feed', '/feeds/posts/default',
                    '/comments/default', '#comment-form', '#comments'
                ]):
                    continue

                # Prüfe auf Paginierungslinks (wichtig für Blogspot!)
                link_text = clean_text(link.get_text()).lower()
                is_pagination = (
                    'updated-max=' in clean_url or # Standard Blogspot Paginierung
                    link_text in ["older posts", "ältere posts", "next page", "nächste seite", "vorherige", "next", "previous", "weiter", "zurück"] or
                    link.get('id') in ['Blog1_blog-pager-older-link', 'Blog1_blog-pager-newer-link'] or # Typische IDs
                    'blog-pager-older-link' in link.get('class', []) or
                    'blog-pager-newer-link' in link.get('class', [])
                )

                # Füge hinzu, wenn es ein normaler interner Link oder ein Paginierungslink ist
                # Optional: Archiv-Links (/YYYY/MM/ Archiv) könnten auch interessant sein
                is_archive = bool(re.search(r'/\d{4}/\d{1,2}/$', clean_url))

                if not clean_url.endswith(('/atom.xml', '/rss.xml')): # Ignoriere explizit Feed-Endungen
                    # Prüfe, ob es ein Label-Link ist - diese SIND nützlich
                    is_label = '/search/label/' in clean_url

                    if is_pagination or is_archive or is_label or not any(c in clean_url for c in ['?', '#']): # Füge normale Links ohne Parameter hinzu ODER Pagin./Archiv/Label
                         # Extra Check: Nicht die aktuelle Seite selbst hinzufügen (manchmal Paginierung)
                         current_parsed = urlparse(base_url)
                         link_parsed = urlparse(clean_url)
                         # Vergleiche Pfad und Query (ohne m=1 Parameter für den Vergleich)
                         current_path_q = current_parsed.path + "?" + "&".join(p for p in current_parsed.query.split('&') if p != 'm=1')
                         link_path_q = link_parsed.path + "?" + "&".join(p for p in link_parsed.query.split('&') if p != 'm=1')
                         if current_path_q.strip('?') != link_path_q.strip('?'):
                              internal_links.add(clean_url)

        except ValueError:
             logging.debug(f"Ungültiger Link ignoriert: {href} auf {base_url}")
        except Exception as e:
             logging.warning(f"Fehler bei Verarbeitung Link '{href}' auf {base_url}: {e}")

    return internal_links


# --- Hauptlogik ---
def main():
    urls_queue = list(START_URLS)
    visited_urls = set(START_URLS)
    all_artworks = []
    processed_artwork_urls = set() # Set zum Verfolgen bereits hinzugefügter Bild-URLs
    pages_processed = 0

    try:
        while urls_queue and pages_processed < MAX_PAGES_TO_VISIT:
            current_url = urls_queue.pop(0)
            logging.info(f"--- Verarbeite Seite {pages_processed + 1}/{MAX_PAGES_TO_VISIT}: {current_url} ---")
            pages_processed += 1

            html_content = get_page_content_requests(current_url)

            if html_content:
                try:
                    # Verwende lxml für potenziell schnelleres/robusteres Parsen, wenn installiert
                    try:
                         import lxml
                         soup = BeautifulSoup(html_content, 'lxml')
                         logging.debug("Using lxml parser.")
                    except ImportError:
                         soup = BeautifulSoup(html_content, 'html.parser')
                         logging.debug("lxml not found, using html.parser.")

                    # 1. Extrahiere Kunstwerkdaten
                    artworks_on_page = extract_artwork_data(soup, current_url)

                    newly_added_count = 0
                    for art in artworks_on_page:
                        artwork_url = art.get("Das ganze Bild als vollen roh link")
                        if artwork_url and artwork_url not in processed_artwork_urls:
                            all_artworks.append(art)
                            processed_artwork_urls.add(artwork_url)
                            newly_added_count += 1
                        elif not artwork_url:
                             logging.warning(f"Kunstwerk ohne Bild-URL gefunden auf {current_url}: {art.get('Name des Werkes')}")
                             # Optional: Solche Einträge trotzdem hinzufügen?
                             # all_artworks.append(art)
                             # newly_added_count += 1
                    if newly_added_count > 0:
                        logging.info(f"{newly_added_count} neue Kunstwerke von dieser Seite hinzugefügt.")


                    # 2. Finde neue interne Links
                    new_links = find_internal_links(soup, current_url)
                    added_to_queue = 0
                    for link in new_links:
                        if link not in visited_urls:
                            visited_urls.add(link)
                            urls_queue.append(link)
                            added_to_queue += 1
                    if added_to_queue > 0:
                        logging.info(f"{added_to_queue} neue Links zur Queue hinzugefügt (Total: {len(urls_queue)}).")

                except Exception as e_parse:
                     logging.error(f"Fehler bei der Verarbeitung/Parsing von {current_url}: {e_parse}", exc_info=True)

            else:
                logging.warning(f"Kein Inhalt für {current_url}. Überspringe.")

            # Wartezeit zwischen Anfragen
            time.sleep(REQUEST_DELAY)

    except KeyboardInterrupt:
        logging.warning("Prozess durch Benutzer unterbrochen.")
    except Exception as e:
        logging.error(f"Ein unerwarteter Fehler im Hauptprozess: {e}", exc_info=True)
    finally:
        # --- Speichern ---
        if all_artworks:
            logging.info(f"--- Prozess beendet. Insgesamt {len(all_artworks)} einzigartige Kunstwerke extrahiert. ---")
            try:
                # Sortieren nach Quelle und dann vielleicht Datum oder Titel?
                # all_artworks.sort(key=lambda x: (x.get('Quell_URL'), x.get('Erscheinungsdatum', '')))
                with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
                    json.dump(all_artworks, f, ensure_ascii=False, indent=4, sort_keys=False)
                logging.info(f"Ergebnisse erfolgreich in '{OUTPUT_JSON_FILE}' gespeichert.")
            except IOError as e:
                logging.error(f"FEHLER beim Speichern der JSON-Datei: {e}")
            except Exception as e:
                 logging.error(f"Unerwarteter FEHLER beim Speichern der JSON-Datei: {e}")
        else:
            logging.warning("Keine Kunstwerkdaten gefunden oder extrahiert.")

# --- Skriptstart ---
if __name__ == "__main__":
    try:
        import requests
        import bs4
    except ImportError:
        logging.error("!!! Bibliotheken 'requests' und 'beautifulsoup4' nicht gefunden.")
        logging.error("!!! Bitte installieren: pip install requests beautifulsoup4")
        # Optional: Empfehlung für lxml
        logging.info("!!! Optional für bessere Performance: pip install lxml")
    else:
        main()
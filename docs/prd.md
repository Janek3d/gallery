# Dokument Wymagań Produktu (PRD) – System "SmartGallery" (MVP)

## 1. Wstęp i Cel Projektu

**Główny problem:** Organizacja i katalogowanie zdjęć jest procesem czasochłonnym, co prowadzi do gromadzenia nieuporządkowanych zbiorów danych ("cyfrowy bałagan"), do których użytkownicy rzadko wracają.

**Cel produktu:** Stworzenie inteligentnej galerii zdjęć w przeglądarce, która automatyzuje proces tagowania i opisywania zdjęć przy użyciu AI, umożliwiając błyskawiczne wyszukiwanie i łatwe udostępnianie wspomnień.

---

## 2. Grupa Docelowa i Persona

* **Użytkownik domowy:** Osoba posiadająca tysiące zdjęć rozproszonych na różnych nośnikach, chcąca szybko odnaleźć konkretne momenty (np. "zdjęcie psa z wakacji") bez ręcznego opisywania każdego pliku.

---

## 3. Zakres Funkcjonalny MVP

### 3.1. Zarządzanie Strukturą

* **Hierarchia:** Galeria -> Album -> Zdjęcie.
* **Wgrywanie (Upload):**
* Pojedyncze pliki (do 5MB) lub paczki ZIP/TAR (do 100MB).
* **Mapowanie folderów:** ZIP wgrany do Galerii tworzy Albumy na podstawie nazw folderów wewnątrz (1 poziom głębokości).
* Obsługa formatów: JPG, PNG, HEIC/HEIF (z automatyczną konwersją do JPG).


* **Masowe działania (Bulk Actions):** Seryjne przenoszenie zdjęć między albumami, usuwanie oraz masowa edycja tagów.

### 3.2. Automatyzacja i AI

* **Obiekty (Yolo):** Automatyczne rozpoznawanie obiektów i przypisywanie tagów (opcjonalne przy uploadzie, możliwe do wyzwolenia później).
* **Tekst (OCR):** Ekstrakcja tekstu ze zdjęć (polski/angielski) w celu umożliwienia wyszukiwania po treści (np. szyldy, dokumenty).
* **Metadane EXIF:** Automatyczne pobieranie danych: data, model aparatu, ISO (opcjonalne, za zgodą użytkownika).
* **Pętla zwrotna:** Usuwanie/edycja tagu przez użytkownika jest sygnałem dla systemu do poprawy algorytmu.

### 3.3. Wyszukiwanie i Przeglądanie

* **Live Search:** Wyszukiwanie po tytułach, tagach AI, tekście z OCR oraz parametrach EXIF (np. ISO).
* **Widok:** Responsywny Grid View z optymalizacją wyświetlania (miniaturki).
* **Ulubione:** System oznaczania zdjęć "gwiazdką".

### 3.4. Udostępnianie i Prywatność

* **Poziomy dostępu:** Galerie Prywatne (domyślne) oraz Publiczne (wyszukiwalne dla wszystkich).
* **Udostępnianie:** Przekazywanie dostępu poprzez adres e-mail. Udostępnione galerie trafiają do sekcji "Udostępnione dla mnie" u odbiorcy (tylko widok).
* **Bezpieczeństwo:** Przycisk "Zgłoś nadużycie" (Report button) w galeriach publicznych.

---

## 4. Specyfikacja Techniczna i Ograniczenia

| Cecha | Specyfikacja |
| --- | --- |
| **Platforma** | Przeglądarka internetowa (RWD) |
| **Storage** | Limit 5GB na użytkownika (wliczając kosz) |
| **Logowanie** | Lokalne konto + Social Login (Google, Facebook itp.) |
| **Usuwanie** | Soft delete (5 dni w koszu), po tym czasie permanentne usunięcie |
| **Eksport** | Paczka ZIP (struktura folderów) + plik JSON z metadanymi |
| **Powiadomienia** | Systemowe (wewnątrz aplikacji) o nowych udostępnieniach |

---

## 5. User Stories

1. **Jako użytkownik**, chcę wgrać cały folder z wakacji w formacie ZIP, aby system automatycznie stworzył mi album o tej samej nazwie.
2. **Jako użytkownik**, chcę wpisać słowo "pizza" w wyszukiwarkę, aby znaleźć zdjęcia z restauracji, mimo że sam ich nie opisałem.
3. **Jako użytkownik**, chcę udostępnić galerię rodzinie po ich mailach, aby tylko oni mogli oglądać moje prywatne zdjęcia.
4. **Jako fotograf-amator**, chcę przefiltrować zdjęcia po ISO 800, aby sprawdzić jakość zdjęć nocnych z mojego aparatu.

---

## 6. Kryteria Sukcesu (KPI)

* **Adopcja:** Średnia liczba zdjęć wgranych przez aktywnego użytkownika w ciągu pierwszego miesiąca.
* **Efektywność AI:** Stosunek tagów zaakceptowanych/pozostawionych przez użytkownika do tagów usuniętych ręcznie.
* **Precyzja wyszukiwania:** Liczba wyszukiwań zakończonych kliknięciem w wynik (zdjęcie).

---

## 7. Zarządzanie Ryzykiem

* **Ryzyko:** Przekroczenie limitu 5GB przez użytkowników domowych.
* **Mitygacja:** Wyraźny wskaźnik zajętości miejsca w UI i proaktywne sugestie czyszczenia kosza.
* **Ryzyko:** Błędna konwersja HEIC.
* **Mitygacja:** Implementacja sprawdzonych bibliotek serwerowych (np. ImageMagick/Libheif) i informowanie o błędach pojedynczych plików.

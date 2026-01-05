import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import requests
from bs4 import BeautifulSoup
import csv
import json
import pandas as pd
import time
from datetime import datetime
import os
from urllib.parse import urljoin

class WebScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Web Scraper")
        self.root.geometry("1200x800")
        
        self.url_var = tk.StringVar(value="https://books.toscrape.com/")
        self.pages_var = tk.IntVar(value=3)
        self.delay_var = tk.DoubleVar(value=1.0)
        self.max_items_var = tk.IntVar(value=50)
        self.format_var = tk.StringVar(value="CSV")
        
        self.scraping_thread = None
        self.is_scraping = False
        self.data = []
        
        self.setup_styles()
        self.create_widgets()
        
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.style.configure('Title.TLabel', font=('Segoe UI', 24, 'bold'))
        self.style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
        self.style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'))
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 20))
        
        ttk.Label(header_frame, text="🌐 WEB SCRAPER", 
                 style='Title.TLabel').pack()
        ttk.Label(header_frame, text="Extract data from any website with intelligent parsing",
                 font=('Segoe UI', 11)).pack(pady=(5, 0))
        
        container = ttk.Frame(main_frame)
        container.pack(fill='both', expand=True)
        
        left_panel = ttk.Frame(container)
        left_panel.pack(side='left', fill='both', padx=(0, 10))
        
        self.create_control_panel(left_panel)
        self.create_status_panel(left_panel)
        self.create_export_panel(left_panel)
        
        right_panel = ttk.Frame(container)
        right_panel.pack(side='right', fill='both', expand=True)
        
        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill='both', expand=True)
        
        self.create_data_tab(notebook)
        self.create_log_tab(notebook)
        self.create_stats_tab(notebook)
        
    def create_control_panel(self, parent):
        control_frame = ttk.LabelFrame(parent, text="⚙️ SCRAPING CONTROLS", padding=15)
        control_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(control_frame, text="Website URL:").grid(row=0, column=0, sticky='w', pady=5)
        
        url_frame = ttk.Frame(control_frame)
        url_frame.grid(row=0, column=1, columnspan=3, sticky='ew', pady=5)
        
        ttk.Entry(url_frame, textvariable=self.url_var, width=50).pack(side='left', fill='x', expand=True)
        ttk.Button(url_frame, text="Test", command=self.test_url, width=8).pack(side='left', padx=(10, 0))
        
        ttk.Label(control_frame, text="Max Pages:").grid(row=1, column=0, sticky='w', pady=5)
        ttk.Spinbox(control_frame, from_=1, to=50, textvariable=self.pages_var, width=15).grid(row=1, column=1, sticky='w', pady=5, padx=5)
        
        ttk.Label(control_frame, text="Max Items:").grid(row=2, column=0, sticky='w', pady=5)
        ttk.Spinbox(control_frame, from_=1, to=500, textvariable=self.max_items_var, width=15).grid(row=2, column=1, sticky='w', pady=5, padx=5)
        
        ttk.Label(control_frame, text="Delay (s):").grid(row=3, column=0, sticky='w', pady=5)
        ttk.Spinbox(control_frame, from_=0.5, to=5.0, increment=0.5, textvariable=self.delay_var, width=15).grid(row=3, column=1, sticky='w', pady=5, padx=5)
        
        ttk.Label(control_frame, text="Format:").grid(row=4, column=0, sticky='w', pady=5)
        ttk.Combobox(control_frame, textvariable=self.format_var,
                    values=["CSV", "JSON", "Excel", "All"], state="readonly", width=15).grid(row=4, column=1, sticky='w', pady=5, padx=5)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=5, column=0, columnspan=4, pady=(20, 0))
        
        self.start_btn = ttk.Button(btn_frame, text="▶ START SCRAPING", 
                                   command=self.start_scraping, style='Accent.TButton')
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹ STOP", 
                                  command=self.stop_scraping, state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="🗑 CLEAR", command=self.clear_data).pack(side='left', padx=5)
        
    def create_status_panel(self, parent):
        status_frame = ttk.LabelFrame(parent, text="📊 STATUS", padding=15)
        status_frame.pack(fill='x', pady=(0, 15))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x', pady=(0, 10))
        
        stats_frame = ttk.Frame(status_frame)
        stats_frame.pack(fill='x')
        
        self.status_label = ttk.Label(stats_frame, text="✅ READY", font=('Segoe UI', 10, 'bold'))
        self.status_label.pack(side='left', padx=(0, 20))
        
        self.count_label = ttk.Label(stats_frame, text="Items: 0")
        self.count_label.pack(side='left', padx=(0, 20))
        
        self.time_label = ttk.Label(stats_frame, text="Time: --")
        self.time_label.pack(side='left')
        
    def create_export_panel(self, parent):
        export_frame = ttk.LabelFrame(parent, text="💾 EXPORT", padding=15)
        export_frame.pack(fill='x')
        
        btn_frame = ttk.Frame(export_frame)
        btn_frame.pack()
        
        ttk.Button(btn_frame, text="📄 CSV", command=lambda: self.save_data('csv')).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="📊 JSON", command=lambda: self.save_data('json')).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="📈 Excel", command=lambda: self.save_data('excel')).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="💎 All", command=lambda: self.save_data('all')).grid(row=0, column=3, padx=5)
        
    def create_data_tab(self, notebook):
        data_frame = ttk.Frame(notebook)
        notebook.add(data_frame, text="📋 DATA")
        
        columns = ('Title', 'Price', 'Rating', 'Availability', 'Category')
        self.tree = ttk.Treeview(data_frame, columns=columns, show='headings', height=25)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(data_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
    def create_log_tab(self, notebook):
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="📝 LOG")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25, font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True)
        
        self.log_message("Ready to start scraping...")
        
    def create_stats_tab(self, notebook):
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="📈 STATS")
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=25, font=('Consolas', 10))
        self.stats_text.pack(fill='both', expand=True)
        
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
    def test_url(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL")
            return
            
        self.log_message(f"Testing URL: {url}")
        self.status_label.config(text="Testing URL...")
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.log_message(f"✅ URL accessible")
                self.status_label.config(text="URL OK")
                messagebox.showinfo("Success", "URL is accessible!")
            else:
                self.log_message(f"❌ HTTP Error: {response.status_code}")
                self.status_label.config(text="HTTP Error")
        except Exception as e:
            self.log_message(f"❌ Error: {str(e)}")
            self.status_label.config(text="Error")
            messagebox.showerror("Error", f"Cannot access URL:\n{e}")
            
    def start_scraping(self):
        if self.is_scraping:
            return
            
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL")
            return
            
        self.data.clear()
        self.tree.delete(*self.tree.get_children())
        self.progress_var.set(0)
        self.count_label.config(text="Items: 0")
        
        self.is_scraping = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        self.scraping_thread = threading.Thread(target=self.scrape_website)
        self.scraping_thread.daemon = True
        self.scraping_thread.start()
        
    def scrape_website(self):
        base_url = self.url_var.get().strip()
        max_pages = self.pages_var.get()
        max_items = self.max_items_var.get()
        delay = self.delay_var.get()
        
        self.log_message(f"🚀 Starting scrape: {max_pages} pages, {max_items} max items")
        self.status_label.config(text="Scraping...")
        
        start_time = time.time()
        total_items = 0
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        for page in range(1, max_pages + 1):
            if not self.is_scraping or total_items >= max_items:
                break
                
            progress = (page / max_pages) * 100
            self.root.after(0, self.progress_var.set, progress)
            
            if page == 1:
                page_url = base_url
            else:
                if "books.toscrape.com" in base_url:
                    page_url = f"{base_url.rstrip('/')}/catalogue/page-{page}.html"
                else:
                    page_url = f"{base_url.rstrip('/')}/page/{page}/"
            
            try:
                response = requests.get(page_url, headers=headers, timeout=10)
                
                if response.status_code != 200:
                    self.log_message(f"⚠️ Page {page}: HTTP {response.status_code}")
                    continue
                
                if "books.toscrape.com" in base_url:
                    items = self.parse_books_toscrape(response.text, base_url)
                else:
                    items = self.parse_general_site(response.text, base_url)
                
                for item in items:
                    if total_items >= max_items:
                        break
                    self.data.append(item)
                    total_items += 1
                    self.root.after(0, self.update_tree, item)
                
                self.root.after(0, self.count_label.config, {"text": f"Items: {total_items}"})
                self.log_message(f"✅ Page {page}: {len(items)} items")
                
                time.sleep(delay)
                
            except Exception as e:
                self.log_message(f"❌ Page {page} failed: {str(e)}")
        
        elapsed = time.time() - start_time
        
        if self.is_scraping:
            self.root.after(0, self.progress_var.set, 100)
            self.status_label.config(text="Complete")
            self.log_message(f"✨ Done! {total_items} items in {elapsed:.1f}s")
            
            if self.data:
                self.root.after(1000, self.auto_save)
                self.generate_statistics()
        
        self.root.after(0, self.reset_ui)
        
    def parse_books_toscrape(self, html_content, base_url):
        soup = BeautifulSoup(html_content, 'html.parser')
        items = []
        
        book_elements = soup.find_all('article', class_='product_pod')
        
        for book in book_elements:
            try:
                title = book.h3.a['title']
                price = book.find('p', class_='price_color').text.strip()
                rating = book.find('p', class_='star-rating')['class'][1]
                availability = book.find('p', class_='instock availability').text.strip()
                
                item = {
                    'title': title,
                    'price': price,
                    'rating': f"{rating}/5",
                    'availability': availability,
                    'category': 'Books',
                    'url': urljoin(base_url, book.h3.a['href']),
                    'scraped_at': datetime.now().isoformat()
                }
                items.append(item)
            except:
                continue
        
        return items
        
    def parse_general_site(self, html_content, base_url):
        soup = BeautifulSoup(html_content, 'html.parser')
        items = []
        
        selectors = [
            'article.product',
            'div.product',
            'li.product',
            'article[class*="product"]',
            'div[class*="product"]',
            'li[class*="product"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                break
        
        if not elements:
            elements = soup.find_all(['div', 'article', 'li'], class_=True)
        
        for element in elements[:20]:
            try:
                title = self.extract_text(element, ['h3', 'h2', 'h1', '.title', '.name'])
                price = self.extract_text(element, ['.price', '.cost', '.amount'])
                
                if not title or not price:
                    continue
                    
                item = {
                    'title': title[:100],
                    'price': price,
                    'rating': 'N/A',
                    'availability': 'N/A',
                    'category': 'General',
                    'url': base_url,
                    'scraped_at': datetime.now().isoformat()
                }
                items.append(item)
            except:
                continue
        
        return items
        
    def extract_text(self, element, selectors):
        for selector in selectors:
            found = element.select_one(selector)
            if found and found.text.strip():
                return found.text.strip()
        return element.text.strip()[:50] if element.text.strip() else ""
        
    def update_tree(self, item):
        self.tree.insert('', 'end', values=(
            item['title'][:40] + '...' if len(item['title']) > 40 else item['title'],
            item['price'],
            item['rating'],
            item['availability'],
            item['category']
        ))
        
    def generate_statistics(self):
        if not self.data:
            return
            
        stats = "📊 SCRAPING STATISTICS\n"
        stats += "=" * 50 + "\n\n"
        stats += f"Total Items: {len(self.data)}\n\n"
        
        price_list = []
        for item in self.data:
            try:
                price_str = item['price'].replace('£', '').replace('$', '').replace(',', '')
                price = float(''.join(c for c in price_str if c.isdigit() or c == '.'))
                price_list.append(price)
            except:
                pass
        
        if price_list:
            stats += f"💰 PRICE ANALYSIS:\n"
            stats += f"  Average: ${sum(price_list)/len(price_list):.2f}\n"
            stats += f"  Highest: ${max(price_list):.2f}\n"
            stats += f"  Lowest: ${min(price_list):.2f}\n"
            stats += f"  Total: ${sum(price_list):.2f}\n"
        
        categories = {}
        for item in self.data:
            cat = item['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        if categories:
            stats += f"\n📚 CATEGORIES:\n"
            for cat, count in categories.items():
                stats += f"  {cat}: {count} items\n"
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)
        
    def reset_ui(self):
        self.is_scraping = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=f"Last: {current_time}")
        
    def stop_scraping(self):
        self.is_scraping = False
        self.status_label.config(text="Stopping...")
        self.log_message("Scraping stopped by user")
        
    def clear_data(self):
        if messagebox.askyesno("Clear Data", "Clear all scraped data?"):
            self.data.clear()
            self.tree.delete(*self.tree.get_children())
            self.count_label.config(text="Items: 0")
            self.progress_var.set(0)
            self.stats_text.delete(1.0, tk.END)
            self.log_message("Data cleared")
            
    def save_data(self, format_type):
        if not self.data:
            messagebox.showwarning("No Data", "Nothing to save!")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("JSON files", "*.json"),
                ("Excel files", "*.xlsx"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        try:
            if format_type == 'csv' or (format_type == 'all' and file_path.endswith('.csv')):
                df = pd.DataFrame(self.data)
                df.to_csv(file_path, index=False, encoding='utf-8')
                self.log_message(f"📄 CSV saved: {os.path.basename(file_path)}")
            elif format_type == 'json' or (format_type == 'all' and file_path.endswith('.json')):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=2, ensure_ascii=False)
                self.log_message(f"📊 JSON saved: {os.path.basename(file_path)}")
            elif format_type == 'excel' or (format_type == 'all' and file_path.endswith('.xlsx')):
                df = pd.DataFrame(self.data)
                df.to_excel(file_path, index=False)
                self.log_message(f"📈 Excel saved: {os.path.basename(file_path)}")
            elif format_type == 'all':
                base = os.path.splitext(file_path)[0]
                df = pd.DataFrame(self.data)
                df.to_csv(base + ".csv", index=False, encoding='utf-8')
                with open(base + ".json", 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=2, ensure_ascii=False)
                df.to_excel(base + ".xlsx", index=False)
                self.log_message(f"💎 All formats saved")
                
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
            self.log_message(f"❌ Save failed: {str(e)}")
            
    def auto_save(self):
        if not self.data:
            return
            
        try:
            os.makedirs("scraped_data", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            df = pd.DataFrame(self.data)
            df.to_csv(f"scraped_data/auto_save_{timestamp}.csv", index=False, encoding='utf-8')
            
            self.log_message(f"💾 Auto-saved: scraped_data/auto_save_{timestamp}.csv")
            
        except Exception as e:
            self.log_message(f"⚠️ Auto-save failed: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = WebScraperGUI(root)
    root.mainloop()
import pandas as pd
import re
import os
from playwright.sync_api import sync_playwright

def run_maps_automation():
    # --- STEP 1: READ INPUT DATA ---
    input_path = "datos_name.xlsx"
    
    if not os.path.exists(input_path):
        print(f"❌ Error: File not found at {input_path}")
        return

    try:
        input_df = pd.read_excel(input_path)
        search_list = input_df['Name'].dropna().unique().tolist()
    except Exception as e:
        print(f"❌ Error reading Excel: {e}")
        return

    total_results = []

    # --- STEP 2: PLAYWRIGHT AUTOMATION ---
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        for business in search_list:
            print(f"\n🔍 Processing: {business}")
            
            try:
                page.goto("https://www.google.com/maps", wait_until="domcontentloaded")
                
                try:
                    page.get_by_role("button", name=re.compile("Aceptar|Agree|Acepto", re.I)).click(timeout=3000)
                except:
                    pass

                search_bar = page.get_by_role("combobox", name=re.compile("Buscar|Search", re.I))
                search_bar.click()
                search_bar.fill(business)
                page.keyboard.press("Enter")

                page.wait_for_selector("h1", timeout=10000)
                
                hours_btn = page.get_by_label(re.compile("horario|hours", re.I)).first
                hours_btn.click()
                
                page.wait_for_selector("table", timeout=5000)
                rows = page.locator("table tr").all()

                for row in rows:
                    cells = row.locator("td").all()
                    if len(cells) >= 2:
                        day = cells[0].inner_text().strip().lower()
                        time = cells[1].inner_text().replace('\u202f', ' ').strip()
                        
                        total_results.append({
                            "Business": business,
                            "Day": day,
                            "Schedule": time
                        })
                print(f"✅ Data extracted for: {business}")

            except Exception as e:
                print(f"⚠️ Skipping {business}: Information not found or timeout.")
                continue

        browser.close()

    # --- STEP 3: DATA TRANSFORMATION & CLEANING ---
    if total_results:
        df_long = pd.DataFrame(total_results)
        df_clean = df_long.drop_duplicates(subset=['Business', 'Day'], keep='first')

        # Create Wide Data Report
        df_wide = df_clean.pivot(index='Business', columns='Day', values='Schedule')

        # Dictionary for bilingual headers
        translation = {
            "lunes": "Lunes / Monday",
            "martes": "Martes / Tuesday",
            "miércoles": "Miércoles / Wednesday",
            "jueves": "Jueves / Thursday",
            "viernes": "Viernes / Friday",
            "sábado": "Sábado / Saturday",
            "domingo": "Domingo / Sunday"
        }

        # Reorder columns and rename them
        days_order = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        existing_cols = [d for d in days_order if d in df_wide.columns]
        
        # Select and reorder
        df_wide = df_wide[existing_cols]
        
        # Rename columns using the dictionary
        df_wide = df_wide.rename(columns=translation)

        # Export result
        output_file = "Restaurant_Data_Wide_Report.xlsx"
        df_wide.to_excel(output_file)
        print(f"\n🚀 PROCESS COMPLETED. Report saved at: {output_file}")
    else:
        print("\n❌ No data was collected.")

if __name__ == "__main__":
    run_maps_automation()
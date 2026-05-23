from parser import parse_all_invoices, save_to_dataframe
from anomaly_detector import run_anomaly_detection, save_results
import os
import pandas as pd

def main():
    print("\n" + "="*50)
    print("  🧾 INVOICE PROCESSING PIPELINE STARTED")
    print("="*50 + "\n")

    # Step 1: Parse all invoices
    print("---> STEP 1: Parsing all invoices...")
    all_invoices = parse_all_invoices()

    if not all_invoices:
        print("No invoices processed ❌. Exiting.")
        return

    # Step 2: Save to DataFrame and CSV
    print(f"\n---> STEP 2: Saving {len(all_invoices)} invoices to CSV...")
    df = save_to_dataframe(all_invoices, save_csv=True)

    print("\n--- Invoice Summary ---")
    print(f"   Total parsed        : {len(df)}")
    print(f"   Passed validation   : {len(df[df['Validation Status'] == 'Passed'])}")
    print(f"   Issues found        : {len(df[df['Validation Status'] == 'Issues Found'])}")

    # Step 3: Run anomaly detection
    print(f"\n---> STEP 3: Running Anomaly Detection...")
    df, duplicates = run_anomaly_detection(df)

    # Step 4: Shows clean summary
    anomalies = df[df['is_anomaly'] == True]
    print(f"\n{'='*50}")
    print(f"📊 FINAL RESULTS SUMMARY")
    print(f"{'='*50}")
    print(f"   Total invoices      : {len(df)}")
    print(f"   Anomalies detected  : {len(anomalies)}")
    print(f"   Clean invoices      : {len(df) - len(anomalies)}")
    print(f"   Duplicate pairs     : {len(duplicates)}")
    print(f"{'='*50}")

    # Step 5: Shows flagged invoices
    if not anomalies.empty:
        print(f"\n🚨 Flagged Invoices:")
        print(anomalies[['Invoice Number', 'Vendor Name',
                         'Total Amount', 'anomaly_reason']].to_string(index=False))
    else:
        print("\n✅ No anomalies detected!")

    # Step 6: Shows duplicates
    if duplicates:
        print(f"\n⚠️ Duplicate Pairs Found:")
        for d in duplicates:
            print(f"   {d['Invoice 1']} & {d['Invoice 2']} "
                  f"(similarity: {d['Similarity Score']}%, "
                  f"amount: {d['Amount']})")
    else:
        print("\n No duplicates found! ✅")

    # Step 7: Save final results
    print(f"\n---> STEP 4: Saving final results...")
    save_results(df, duplicates)

    # Save final combined CSV
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    final_csv = os.path.join(output_dir, 'final_results.csv')
    df[['Filename', 'Invoice Number', 'Vendor Name',
        'Total Amount', 'is_anomaly',
        'anomaly_reason']].to_csv(final_csv, index=False)
    print(f"✅ Final CSV saved to: output/final_results.csv")

    print("\n" + "="*50)
    print("  PIPELINE COMPLETE!")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
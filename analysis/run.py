import os
import pandas as pd

from utils import add_dists, add_metrics, get_deviation_std_norm_dist, indicies
from MongoRepository import MongoRepository

repo = MongoRepository(
    f"mongodb+srv://weidinger:{os.environ['WOHNUNGSGSCHICHTEN_ATLAS_PW']}@cluster0.sh9uc.mongodb.net/?retryWrites=true&w=majority")
flats = repo.get_latest_flats()
df = pd.DataFrame(flats)
print(f"Got {len(flats)} entries")

# Dynamic distance fetching
if 'distance_tu' not in df.columns:
    print('Add distance column for processing')
    df[indicies] = None
affected_entries = df['distance_tu'].isnull()
if affected_entries.any():
    df_no_distance = df[affected_entries]

    print(f"{len(df_no_distance)} entries with no distance found")
    df_no_distance = add_dists(df_no_distance)

    df.loc[affected_entries, indicies] = df_no_distance[indicies]
    count = repo.update_all(df_no_distance.to_dict('records'), indicies)
    print(f"Updated {count} entries in the DB")


add_metrics(df)
# plot_norm_dists(df)

# Calculate attribute scores
df['score'] = 0
df['score'] += get_deviation_std_norm_dist(df['mean_ppms'])
df['score'] += get_deviation_std_norm_dist(df['distance'])
df[df['rooms'] == 3]['score'] += 2
count = repo.update_all(df.to_dict('records'), [
                        'ppms', 'ppms_free', 'mean_ppms', 'distance', 'score'])
print(f"Updated {count} entries in the DB")


print(df.sort_values('score', ascending=False))
urls = df.sort_values('score', ascending=False)['seo_url'][:10]
print("\n".join([f"https://www.willhaben.at/{x}" for x in urls.values]))


print()

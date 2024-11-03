
from selenium import webdriver
import time
import bs4 as bs
import io
import pandas as pd
from itertools import combinations, permutations
import scraper


POS_SHELL = [(1,	'PG', None	),
    (2,	'SG', None	),
    (3,	'SF', None	),
    (4,	'PF', None	),
    (5,	'C', None	),
    (6,	'SG', 'PG'),
    (7,	'SF', 'PF'),
    (8,	'PF', 'C'),]

shell = pd.DataFrame(POS_SHELL)
shell.columns = ['slot','pos_1', 'pos_2']
shell = pd.melt(shell, id_vars='slot', value_name='pos').drop(columns='variable').dropna()

# grab the html for the current team score page AND the expanded team score page
sources_core = scraper.get_sources(scraper.coreteam_scoreurl)
sources_exp = scraper.get_sources(scraper.expteam_scoreurl)

# collect all league player names and clean them
wtf = scraper.get_sources({'all':scraper.all_url})['all']

soup = bs.BeautifulSoup(scraper.get_sources({'all':scraper.all_url})['all'])
tabs = soup.find_all('tbody')

players = []
for tab in tabs:
    if tabs.index(tab) == len(tabs) - 1:    
        table_rows = tab.find_all('tr')
        for tr in table_rows:
            player = scraper.player_cleaner(tr.text.split('\n')[2])             
            players.append(player.rstrip())

def namecleaner(r):
    for p in players:
        if p in r.upper():             
            return p


# parse player scores
def parser(sources_dict, schedurl):
    scores = dict()
    rostered = []
    
    for key, src in sources_dict.items():
        if key in('allplayers','sched'): continue
        
        soup = bs.BeautifulSoup(sources_dict[key])
        tables = soup.find_all('table')    
        
        scores[key] = []
        if key == 's2025proj':
            scores['player'] = []
        
        for table in tables:
            table_rows = table.find_all('tr')
            
            if tables.index(table) == 0 and key == 's2025proj':
                for tr in table_rows:            
                    td = tr.find_all('td')
                    if len(td) > 0:            
                        if schedurl == scraper.coreteam_schedurl:
                            rostered.append(td[1].text)
                            scores['player'].append(namecleaner(td[1].text))
                        else:
                            rostered.append(td[0].text)                            
                            scores['player'].append(namecleaner(td[0].text))
            
            if tables.index(table) == 2:
                for tr in table_rows:            
                    td = tr.find_all('td')
                    
                    if len(td) == 2:
                        scores[key].append(pd.to_numeric(td[1].text, errors='coerce'))  
                
    scores = pd.DataFrame(scores).dropna()
    
    soup = bs.BeautifulSoup(scraper.get_sources({'all':schedurl})['all'])
    table = soup.find('table')
    
    sched = []
    
    table_rows = table.find_all('tr')
    for tr in table_rows:            
        td = tr.find_all('td')
        
        if len(td) > 0:    
            schedp = [i.text.replace('--','') for i in td[4:]]
            schedp = len([s for s in schedp if len(s) > 0])
            sched.append(schedp)
    
    
    rostered_clean = []
    
    for r in rostered:
        for p in players:
            if p in r.upper():             
                leftover = r.upper().replace(p, '')            
                positions = scraper.position_cleaner(leftover)
                rostered_clean.append([p, *positions])
    
    
    for i in range(len(rostered_clean)):
        rostered_clean[i].append(sched[i])
    
    
    indf = pd.DataFrame(rostered_clean, columns=['player','pos_1','pos_2','games'])
    indf = indf.merge(scores.fillna(0))
    
    return indf



coredf = parser(sources_core, scraper.coreteam_schedurl)
coredf['exp'] = 0
expdf = parser(sources_exp, scraper.expteam_schedurl)
expdf['exp'] = 1



#expdf = expdf.head(15)
superscore = pd.concat([coredf, expdf])

#superscore = coredf.copy()

superscore['elig'] = 1.0
superscore.loc[superscore.player == 'DEVIN VASSELL', 'elig'] = 0.0
superscore.loc[superscore.player == 'MARK WILLIAMS', 'elig'] = 0.0
superscore.loc[superscore.player == 'SHAEDON SHARPE', 'elig'] = 0.0
superscore.loc[superscore.player == 'Isaiah Hartenstein'.upper(), 'elig'] = 0.0

superscore.loc[superscore.s2024 == 0, 's2024'] = None
superscore['s2024'] = superscore['s2024'].fillna(superscore.s2025proj)

superscore['7'] = 0
superscore['l15'] = 0
superscore['l30'] = 0

superscore['tot_pts'] = (superscore.games ** 0.85) * ((\
                                        (superscore.l7 * 3) + \
                                        (superscore.l15 * 3) + \
                                        (superscore.l30 * 2) + \
                                        superscore.s2024 + superscore.s2025+ superscore.s2025proj/0.5 )\
                                          /10.5) * superscore.elig

superscore = superscore.loc[superscore.elig > 0]
superscore = superscore.loc[~((superscore.exp == 1) & (superscore.s2025proj < 25))]


players = pd.melt(superscore[['player','tot_pts','pos_1','pos_2','exp']], id_vars=['player','tot_pts','exp'])
players = players.drop(columns='variable').rename(columns={'value':'pos'})
players.pos = players.pos.str.upper()
players = players.dropna()

out = players.merge(shell)
out = out.sort_values(by=['slot','tot_pts'], ascending=[True,False])
out = out.drop_duplicates(subset=['player','slot'])


INCL_FO_SHO = [('SHAI GILGEOUS-ALEXANDER',6),
                ('LEBRON JAMES',7),
                 ('ALPEREN SENGUN',5),
                 ('LAMELO BALL',1)]

INCL_FO_SHO = sorted(INCL_FO_SHO, key=lambda tup: tup[1])

INCL_FO_SHO=[]

player_list = superscore.loc[~superscore.player.isin([p[0] for p in INCL_FO_SHO])].player.tolist()
perms_cnt = permutations(player_list, 8 - len(INCL_FO_SHO))
perms = permutations(player_list, 8 - len(INCL_FO_SHO))
perms_len = sum(1 for _ in perms_cnt)

print(f'Hacking through {perms_len:,} iterations')

winners = []

batch_size = 1_000_000
i = 0
hasvals = True

MAXEXP = 2

while hasvals:
    try:
        combos_raw = [next(perms) for _ in range(batch_size)]
    except:
        combos_raw = list(perms)
        hasvals = False
    
    combos_batch = []
    for c in combos_raw:
        it_c = iter(c)        
        outc = []
        for i in range(8):
            outp = [p for p in INCL_FO_SHO if p[1] - 1 == i]
            if len(outp) == 1:
                outp = outp[0][0]
            else:
                outp = next(it_c)
                
            outc.append(outp)
        
        combos_batch.append(outc)
            
    combos_batch = pd.DataFrame(combos_batch)
    combos_batch.columns += 1
    combos_batch['it'] = combos_batch.index
    
    combos_batch = pd.melt(combos_batch, id_vars=['it'], var_name='slot', value_name='player')
    combos_batch = combos_batch.merge(out)
    
    combos_batch = combos_batch.sort_values(by=['it','slot'])
    combos_batch['n'] = combos_batch.groupby('it')['player'].transform('count')
    combos_batch['exp_tot'] = combos_batch.groupby('it')['exp'].transform('sum')
    combos_batch = combos_batch.loc[(combos_batch['n'] == 8) & (combos_batch.exp_tot <= MAXEXP)]
    combos_batch.sort_values(by=['it','slot'])
    combos_batch['it_sum'] = combos_batch.groupby('it')['tot_pts'].transform('sum')
    
    win_batch = combos_batch.loc[combos_batch.it_sum == combos_batch.it_sum.max()]
    
    winners.append(win_batch)
    
    i += 1
    print(i * batch_size, 'done...')
    
winners = pd.concat(winners)


winners = winners.loc[winners.it_sum == winners.it_sum.max()]
winners['exp'] = winners.player.isin(expdf.player) * 1

selection = winners.loc[winners.it == winners.it.min()]


print(selection.drop(columns='exp_tot'))

print(players.groupby('pos').agg({'pos':'count','tot_pts':'mean'}).sort_values(by='tot_pts').round(1))

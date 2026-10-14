#!/usr/bin/env python3
"""Exercise the actual NPC pool functions with LP64 derived actors under sanitizers."""
from pathlib import Path
import subprocess
import tempfile
import sys
root=Path(__file__).resolve().parents[2]
source=(root/'src/actor/npc/ac_npc_ctrl.c_inc').read_text()
def function(name):
 start=source.index('static ',source.index(name)-20)
 end=source.index('{',start)+1;depth=1
 while depth:
  if source[end]=='{':depth+=1
  elif source[end]=='}':depth-=1
  end+=1
 return source[start:end]
pre='''#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include "ac_npc_station_master.h"
#include "ac_npc_shop_common.h"
#include "ac_npc_rcn_guide.h"
static struct {NPC_ACTOR *keep_actors[9]; int keep_actor_used[9];} pool;
#define CLIP(x) (&pool)
int g_pc_verbose;
#define aNPC_ACTOR_CLASS_SLOT_SIZE 0x2000
static struct {u64 align; u8 buf[aNPC_ACTOR_CLASS_SLOT_SIZE + 15];} aNPC_n_actor_cl_tbl[9];
'''
functions='\n'.join(function(n) for n in ['aNPC_get_actor_area_proc','aNPC_free_actor_area_proc','aNPC_keep_actor_class','aNPC_free_actor_class'])
main='''int main(void) {
 aNPC_keep_actor_class();
 assert(!aNPC_get_actor_area_proc(aNPC_ACTOR_CLASS_SLOT_SIZE+1,"oversize",1));
 size_t sizes[]={sizeof(NPC_STATION_MASTER_ACTOR),sizeof(NPC_SHOP_COMMON_ACTOR),sizeof(NPC_RCN_GUIDE_ACTOR),aNPC_ACTOR_CLASS_SLOT_SIZE};
 for(int i=0;i<9;i++) {void *p=aNPC_get_actor_area_proc(sizes[i%4],"test",1);assert(p);assert(((uintptr_t)p & 15)==0);memset(p,0xa5,sizes[i%4]);}
 assert(!aNPC_get_actor_area_proc(sizeof(NPC_ACTOR),"full",1));
 aNPC_free_actor_area_proc((ACTOR*)pool.keep_actors[3]);assert(!pool.keep_actor_used[3]);
 assert(aNPC_get_actor_area_proc(sizeof(NPC_SHOP_COMMON_ACTOR),"reuse",1));
 for(int i=0;i<9;i++)aNPC_free_actor_area_proc((ACTOR*)pool.keep_actors[i]);
 aNPC_free_actor_class();
 aNPC_keep_actor_class();assert(aNPC_get_actor_area_proc(sizeof(NPC_STATION_MASTER_ACTOR),"teardown",1));aNPC_free_actor_class();
 return 0;
}
'''
temporary = tempfile.TemporaryDirectory(prefix='ac-npc-pool-')
p=Path(temporary.name)/'check.c';p.write_text(pre+functions+main)
binary = str(Path(temporary.name)/'check')
subprocess.run([sys.argv[1] if len(sys.argv)>1 else 'cc','-g','-fsanitize=address,undefined','-DTARGET_PC','-D_LANGUAGE_C','-DF3DEX_GBI_2','-DVERSION=0','-I'+str(root/'include'),'-I'+str(root/'pc/include'),str(p),'-o',binary],check=True)
subprocess.run([binary],check=True)
print('Actual NPC pool functions: derived-size persistent slots, ninth-slot limit, reuse, cleanup passed ASan/UBSan')

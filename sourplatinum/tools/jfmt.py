# JSON serializer that reproduces the repo's hand-formatted JSON styles (see CLAUDE.md, "JSON formatting").
import json
def _scalar(v): return json.dumps(v, ensure_ascii=False)
def dumps(obj, inline_pred, indent=4, empty_list={}, empty='[  ]'):
    def rec(v, path, lvl):
        pad=' '*(indent*lvl); pad1=' '*(indent*(lvl+1))
        if isinstance(v, dict):
            if not v: return '{}'
            items=[f'{pad1}{_scalar(k)}: {rec(x, path+(k,), lvl+1)}' for k,x in v.items()]
            return '{\n'+',\n'.join(items)+'\n'+pad+'}'
        if isinstance(v, list):
            if not v: return empty_list.get(path,empty)
            if inline_pred(path, v):
                return '[ '+', '.join(rec(x,path+('[]',),lvl) for x in v)+' ]'
            return '[\n'+',\n'.join(pad1+rec(x,path+('[]',),lvl+1) for x in v)+'\n'+pad+']'
        return _scalar(v)
    return rec(obj, (), 0)

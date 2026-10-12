"""Evidence-first extraction of explicit component/transport statements in RFPs."""
import re

ROLE_PATTERN = r'(?:[\u4e00-\u9fffA-Za-z0-9_]{0,10}\s*(?:API|系统|服务|仓储|网关|数据库|前端|客户端|门户)|SQLite|PostgreSQL|MySQL|Redis|Kafka|RabbitMQ|本地模型|大语言模型)'


def extract_rfp(files):
    nodes, edges, statements, sections = {}, {}, [], []
    def clean(value):
        value = re.sub(r'\s+', '', value).strip('：:、，。()（） ')
        for prefix in ('图中应包含','外部系统包括','建设','提供','协调','通过','请求','调用','使用','到','向','与','及','和','每个','本','该'):
            if value.startswith(prefix) and len(value)>len(prefix):
                value=value[len(prefix):]
        return value
    def kind(name):
        if name in ('SQLite','PostgreSQL','MySQL','Redis') or '数据库' in name:
            return 'database'
        if name in ('Kafka','RabbitMQ'):
            return 'messagebus'
        if re.search('客户端|前端|门户|网页|浏览器',name):
            return 'frontend'
        if re.search('模型',name):
            return 'model'
        if name.endswith(('系统','网关')):
            return 'external'
        return 'backend'
    def add_node(name, evidence):
        name=clean(name)
        if not name or name in ('系统','服务','API','仓储','数据库','客户端系统','测试系统','外部系统','目标系统') or len(name)>24:
            return None
        if name not in nodes:
            nodes[name]=dict(id='rfp-'+str(len(nodes)),name=name,sub={'frontend':'用户入口','backend':'应用组件','external':'外部依赖','database':'持久化存储','model':'模型推理','messagebus':'异步消息'}[kind(name)],type=kind(name),x=0,y=0,evidence=[evidence],confidence='confirmed')
        return name
    for file in files:
        section='';page=None
        for lineno,line in enumerate(file['text'].splitlines(),1):
            pm=re.search(r'\[第 (\d+) 页\]',line)
            if pm:
                page=int(pm[1]);continue
            if line.startswith('#'):
                section=line.strip('# ');sections.append(section);continue
            if not line.strip():
                continue
            evidence={'file':file['name'],'line':lineno,'quote':line.strip()[:700]}
            if page:
                evidence['page']=page
            future=bool(re.search('生产要求|测试边界|验收|状态|异常|目标与范围',section))
            if future:
                continue
            text=re.sub(r'\s+(?=API)', '', re.sub(r'^\s*\d+[.、]\s*','',line).strip())
            current=None
            lead=re.match(r'^([^：:]{1,20})[：:]',text)
            if lead and re.fullmatch(ROLE_PATTERN,lead[1].strip()):
                current=add_node(lead[1],evidence)
            # Split verbs before recognizing noun phrases, preventing actions becoming nodes.
            fragments=re.split(r'[，。；、：:\s]+|通过|请求|调用|使用|提供|协调|建设|包括|完成|提交|接收|返回|保存|发起|成功后|发货后|支付后|以及|到|向|与|及|和|的',text)
            for fragment in fragments:
                if re.fullmatch(ROLE_PATTERN,fragment or ''):
                    add_node(fragment,evidence)
            statements.append((text,current,evidence))
    # Generic references such as 服务/API/仓储 are only bound when unique.
    aliases={name:name for name in nodes}
    for short in ('API','服务','仓储'):
        candidates=[name for name in nodes if name.endswith(short)]
        if len(candidates)==1:
            aliases[short]=candidates[0]
    alias_pattern='|'.join(re.escape(a) for a in sorted(aliases,key=len,reverse=True)) or r'(?!)'
    def mentions(text):
        return [(m.start(),m.end(),aliases[m.group()]) for m in re.finditer(alias_pattern,re.sub(r'\s+(?=API)','',text))]
    def add_edge(source,target,label,protocol,port,ev):
        if not source or not target or source==target:
            return
        a,b=nodes[source],nodes[target];key=(a['id'],b['id'],protocol,port)
        if key not in edges:
            edges[key]=dict(id='rfp-edge-'+str(len(edges)),source=a['id'],target=b['id'],label=label,protocol=protocol,port=port,style='solid',evidence=[ev],confidence='confirmed')
        elif ev not in edges[key]['evidence']:
            edges[key]['evidence'].append(ev)
    for text,current,evidence in statements:
        text=re.sub(r'\s+(?=API)','',text)
        body=text.split('：',1)[-1] if current else text
        for clause in re.split('[。；]',body):
            pairs=list(re.finditer('('+alias_pattern+r')\s*(?:到|→|->|向)\s*('+alias_pattern+')',clause))
            for pair in pairs:
                a,b=aliases[pair[1]],aliases[pair[2]]
                local='进程内' in clause
                file_access=nodes[b]['type']=='database' and ('文件' in clause or b=='SQLite')
                add_edge(a,b,'进程内调用' if local else '本地文件访问' if file_access else '调用','进程内' if local else 'SQLite 文件' if file_access else '', '不适用' if local or file_access else '',evidence)
            network=re.search(r'通过\s*(HTTPS?|gRPC|TCP|AMQP)\s*(?:调用|请求)?',clause,re.I)
            if network:
                before=mentions(clause[:network.start()]);after=mentions(clause[network.end():])
                source=before[-1][2] if before else current
                target=after[0][2] if after else current
                if source==target and current:
                    source=before[-1][2] if before else None
                port=re.search(r'(?:目标端口|端口)\s*[:：]?\s*(\d{2,5})',clause)
                route=re.search(r'\b(GET|POST|PUT|DELETE|PATCH)\s+(/[^，。；\s]+)',clause)
                add_edge(source,target,route.group() if route else '接口调用',network[1].upper(),port[1] if port else '',evidence)
            db=re.search(r'使用\s*(SQLite|MySQL|PostgreSQL|Redis)',clause,re.I)
            if db:
                before=mentions(clause[:db.start()]);source=before[-1][2] if before else current;target=next((n for n in nodes if n.lower()==db[1].lower()),None)
                if source and target:
                    filename=re.search(r'\b([\w.-]+\.db)\b',clause)
                    if filename:
                        nodes[target]['sub']=filename[1]
                    add_edge(source,target,'读写本地文件' if target=='SQLite' else '数据访问','SQLite 文件' if target=='SQLite' else '', '不适用' if target=='SQLite' else '',evidence)
    title=next((s for s in sections if 'RFP' in s or '需求' in s),files[0]['name'].rsplit('.',1)[0] if files else '需求架构')
    questions=[]
    for file in files:
        for line in file['text'].splitlines():
            if re.search('生产版本|还需|未实现|待实现|待确认',line):
                questions.append(line.strip())
    return dict(title=re.sub(r'[（(]测试资料[）)]','',title).strip(),nodes=list(nodes.values()),edges=list(edges.values()),warnings=questions,coverage=[{'file':f['name'],'status':'analyzed','method':'需求证据抽取'} for f in files])

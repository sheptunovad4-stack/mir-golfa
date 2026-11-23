import React, { useMemo, useState } from 'react';
import golfData from './data/golf-data';
import resultsArchive from './data/archive-rebuild/student-golf-seed.json';
import { SafeAreaView, View, Text, ScrollView, Pressable, TextInput, Linking, StatusBar } from 'react-native';

const COLORS = {
  bg: '#F4F5EF', card: '#FFFFFF', ink: '#182820', muted: '#6C776F',
  green: '#174D38', lime: '#D8F078', line: '#E0E5DC', amber: '#F3B94E'
};

const EVENTS = (golfData.tournaments || []).map((e, i) => ({
  id: e.id || `tournament-${i}`,
  name: e.name || 'Турнир без названия',
  dates: e.dates || [e.start, e.end].filter(Boolean).join(' — ') || 'Дата не указана',
  start: e.start || '',
  end: e.end || '',
  location: e.location || e.venue || e.region || e.country || 'Место уточняется',
  level: e.level || e.code || 'Не указан',
  sport: e.sport || 'Гольф',
  status: e.status || (e.end && e.end < '2026-11-23' ? 'Завершён' : 'В календаре'),
  organizer: e.organizer || '',
  source: e.source || 'https://rusgolf.ru/ru/contests',
  note: e.note || e.sourceName || 'Сведения собраны из указанного источника; актуальность проверяйте у организатора.'
}));

const SOURCES = (golfData.sources || []).map(s => ({
  name: s.name || 'Источник',
  country: s.country || 'Не указано',
  type: s.roles || s.type || 'Информация о гольфе',
  url: s.url || '',
  status: s.status || 'Добавлен в реестр',
  trust: s.owner === 'федерация' ? 5 : (s.owner === 'клуб' ? 4 : 3),
  note: s.note || ''
}));

const CLUBS = golfData.clubs || [];
const ARCHIVE = resultsArchive.tournaments || [];

function Pill({children, dark=false}) {
  return <View style={{backgroundColor: dark ? COLORS.green : '#E8EDE3', paddingHorizontal:10, paddingVertical:6, borderRadius:30}}>
    <Text style={{color:dark?'white':COLORS.green, fontSize:11, fontWeight:'700'}}>{children}</Text>
  </View>;
}

function EventCard({event, onPress}) {
  return <Pressable onPress={onPress} style={{backgroundColor:COLORS.card, borderRadius:22, padding:17, marginBottom:12, borderWidth:1, borderColor:COLORS.line}}>
    <View style={{flexDirection:'row', justifyContent:'space-between', alignItems:'center', marginBottom:12}}>
      <Pill>{event.sport}</Pill><Text style={{fontSize:11, color:COLORS.muted}}>{event.level}</Text>
    </View>
    <Text style={{fontSize:19, lineHeight:24, color:COLORS.ink, fontWeight:'800', marginBottom:8}}>{event.name}</Text>
    <Text style={{fontSize:14, color:COLORS.green, fontWeight:'700', marginBottom:5}}>◷  {event.dates}</Text>
    <Text style={{fontSize:13, lineHeight:19, color:COLORS.muted, marginBottom:13}}>⌖  {event.location}</Text>
    <View style={{flexDirection:'row', alignItems:'center', justifyContent:'space-between'}}>
      <Pill dark>{event.status}</Pill>
      <Text style={{fontSize:12, fontWeight:'700', color:COLORS.green}}>Подробнее ↗</Text>
    </View>
  </Pressable>;
}

export default function App() {
  const [tab, setTab] = useState('Турниры');
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(null);
  const [filter, setFilter] = useState('Все');
  const [saved, setSaved] = useState([]);

  const shown = useMemo(() => EVENTS.filter(e => {
    const text = (e.name + ' ' + e.location + ' ' + e.sport + ' ' + e.level).toLowerCase();
    const matches = text.includes(query.toLowerCase());
    const category = filter === 'Все' || (filter === 'Гольф' && e.sport === 'Гольф') || (filter === 'Мини-гольф' && e.sport === 'Мини-гольф');
    return matches && category;
  }), [query, filter]);

  const openSource = (url) => Linking.openURL(url).catch(() => {});
  const toggleSave = (id) => setSaved(old => old.includes(id) ? old.filter(x => x !== id) : [...old, id]);

  return <SafeAreaView style={{flex:1, backgroundColor:COLORS.bg}}>
    <StatusBar barStyle="dark-content" />
    <View style={{paddingHorizontal:20, paddingTop:12, paddingBottom:14}}>
      <View style={{flexDirection:'row', justifyContent:'space-between', alignItems:'center'}}>
        <View>
          <Text style={{fontSize:12, color:COLORS.muted, letterSpacing:2, fontWeight:'700'}}>GOLF • CIS</Text>
          <Text style={{fontSize:30, color:COLORS.ink, fontWeight:'900', marginTop:3}}>Поле событий.</Text>
        </View>
        <View style={{width:48, height:48, borderRadius:17, backgroundColor:COLORS.lime, alignItems:'center', justifyContent:'center'}}>
          <Text style={{fontSize:24}}>⛳</Text>
        </View>
      </View>
      <Text style={{fontSize:13, color:COLORS.muted, marginTop:8}}>Турниры, результаты и требования — в одном месте.</Text>
    </View>

    {selected ? <ScrollView contentContainerStyle={{padding:20, paddingTop:4}}>
      <Pressable onPress={() => setSelected(null)} style={{marginBottom:18}}><Text style={{color:COLORS.green, fontWeight:'800'}}>← Все турниры</Text></Pressable>
      <View style={{backgroundColor:COLORS.green, borderRadius:24, padding:20, marginBottom:14}}>
        <Pill dark>{selected.sport} · {selected.level}</Pill>
        <Text style={{fontSize:26, color:'white', fontWeight:'900', lineHeight:32, marginTop:14}}>{selected.name}</Text>
        <Text style={{fontSize:15, color:'#E3EBDD', marginTop:12}}>◷  {selected.dates}</Text>
        <Text style={{fontSize:14, color:'#E3EBDD', marginTop:6}}>⌖  {selected.location}</Text>
      </View>
      <View style={{backgroundColor:COLORS.card, padding:18, borderRadius:20, borderWidth:1, borderColor:COLORS.line, marginBottom:12}}>
        <Text style={{fontWeight:'800', color:COLORS.ink, fontSize:16, marginBottom:8}}>Статус и организатор</Text>
        <Text style={{color:COLORS.muted, lineHeight:21}}>{selected.status}</Text>
        <Text style={{color:COLORS.muted, lineHeight:21, marginTop:5}}>{selected.organizer || 'Организатор уточняется'}</Text>
      </View>
      <View style={{backgroundColor:COLORS.card, padding:18, borderRadius:20, borderWidth:1, borderColor:COLORS.line, marginBottom:12}}>
        <Text style={{fontWeight:'800', color:COLORS.ink, fontSize:16, marginBottom:8}}>Важная заметка</Text>
        <Text style={{color:COLORS.muted, lineHeight:22}}>{selected.note}</Text>
        <Text style={{fontSize:12, color:COLORS.muted, marginTop:12}}>Победитель, счёт и требования не добавляются без подтверждённого протокола.</Text>
      </View>
      <Pressable onPress={() => openSource(selected.source)} style={{backgroundColor:COLORS.lime, padding:16, borderRadius:16, alignItems:'center', marginBottom:12}}>
        <Text style={{fontWeight:'900', color:COLORS.ink}}>Открыть первоисточник ↗</Text>
      </Pressable>
      <Pressable onPress={() => toggleSave(selected.id)} style={{borderColor:COLORS.green, borderWidth:1, padding:15, borderRadius:16, alignItems:'center'}}>
        <Text style={{fontWeight:'800', color:COLORS.green}}>{saved.includes(selected.id) ? '★ В избранном' : '☆ Добавить в избранное'}</Text>
      </Pressable>
    </ScrollView> : <ScrollView contentContainerStyle={{paddingHorizontal:20, paddingBottom:110}}>
      {tab === 'Турниры' && <>
        <View style={{backgroundColor:COLORS.green, borderRadius:24, padding:18, marginBottom:18}}>
          <Text style={{color:COLORS.lime, fontSize:11, fontWeight:'800', letterSpacing:1.5}}>ОБЗОР КАЛЕНДАРЯ</Text>
          <Text style={{fontSize:24, color:'white', fontWeight:'900', lineHeight:29, marginTop:8}}>Следи за игрой.{'\n'}Не пропускай старт.</Text>
          <Text style={{fontSize:13, lineHeight:20, color:'#E1E8DF', marginTop:8}}>Календарь и справочники загружены из исследовательского архива проекта.</Text>
          <View style={{flexDirection:'row', gap:8, marginTop:16}}>
            <View style={{backgroundColor:'#FFFFFF18', padding:11, borderRadius:14, flex:1}}>
              <Text style={{fontSize:22, color:'white', fontWeight:'900'}}>{EVENTS.filter(e=>e.status==='Предстоит' || e.status==='В календаре').length}</Text>
              <Text style={{fontSize:11, color:'#E1E8DF'}}>Предстоящих</Text>
            </View>
            <View style={{backgroundColor:'#FFFFFF18', padding:11, borderRadius:14, flex:1}}>
              <Text style={{fontSize:22, color:'white', fontWeight:'900'}}>{SOURCES.length}</Text>
              <Text style={{fontSize:11, color:'#E1E8DF'}}>Источника</Text>
            </View>
          </View>
        </View>
        <TextInput value={query} onChangeText={setQuery} placeholder="Поиск турнира, города, уровня…" placeholderTextColor="#89938B" style={{backgroundColor:COLORS.card, borderWidth:1, borderColor:COLORS.line, borderRadius:15, paddingHorizontal:15, paddingVertical:13, fontSize:14, marginBottom:12, color:COLORS.ink}}/>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{marginBottom:14, maxHeight:42}}>
          {['Все','Гольф','Мини-гольф'].map(f => <Pressable key={f} onPress={() => setFilter(f)} style={{marginRight:8}}><Pill dark={filter===f}>{f}</Pill></Pressable>)}
        </ScrollView>
        <View style={{flexDirection:'row', alignItems:'center', justifyContent:'space-between', marginBottom:12}}>
          <Text style={{fontSize:19, color:COLORS.ink, fontWeight:'900'}}>Календарь</Text>
          <Text style={{fontSize:12, color:COLORS.muted}}>{shown.length} турниров</Text>
        </View>
        {shown.map(event => <EventCard key={event.id} event={event} onPress={() => setSelected(event)} />)}
        <Text style={{fontSize:11, lineHeight:17, color:COLORS.muted, marginTop:3}}>Демо не является гарантией актуальности. Даты и статусы нужно перепроверять у организаторов перед регистрацией или поездкой.</Text>
      </>}
      {tab === 'Аналитика' && <>
        <Text style={{fontSize:24, fontWeight:'900', color:COLORS.ink, marginBottom:8}}>Аналитика</Text>
        <Text style={{fontSize:13, color:COLORS.muted, lineHeight:20, marginBottom:16}}>Пока это каркас будущей аналитики. Автоматические выводы появятся после подключения базы и ежедневных сборщиков.</Text>
        {[
          ['Календарь','Сравнение количества турниров по месяцам, странам и уровням.'],
          ['Результаты','История победителей, мест и счёта по официальным протоколам.'],
          ['Изменения','Новые даты, переносы, изменения правил и сроков регистрации.'],
          ['ИИ-обзоры','Короткие статьи с кликабельными источниками для каждого факта.']
        ].map(([title,desc]) => <View key={title} style={{backgroundColor:COLORS.card, borderRadius:18, padding:17, marginBottom:10, borderWidth:1, borderColor:COLORS.line}}><Text style={{fontWeight:'900', color:COLORS.ink, fontSize:16}}>{title}</Text><Text style={{color:COLORS.muted, lineHeight:20, marginTop:6}}>{desc}</Text></View>)}
      </>}
      {tab === 'Архив' && <>
        <Text style={{fontSize:24, fontWeight:'900', color:COLORS.ink, marginBottom:8}}>Архив результатов</Text>
        <Text style={{fontSize:13, color:COLORS.muted, lineHeight:20, marginBottom:16}}>Сохранены опубликованные места и счёт. Частичные и предварительные результаты помечены отдельно и не выдаются за полные официальные протоколы.</Text>
        {ARCHIVE.map(t => <View key={t.id} style={{backgroundColor:COLORS.card, borderRadius:18, padding:17, marginBottom:12, borderWidth:1, borderColor:COLORS.line}}>
          <Text style={{fontSize:11, color:COLORS.green, fontWeight:'800'}}>{t.year} · {t.resultCoverage || 'результаты'}</Text>
          <Text style={{fontSize:17, color:COLORS.ink, fontWeight:'900', marginTop:5}}>{t.name}</Text>
          <Text style={{fontSize:12, color:COLORS.muted, marginTop:4}}>{t.venue || 'Место не указано'} · {t.country || 'Страна не указана'}</Text>
          <Text style={{fontSize:12, color:COLORS.muted, marginTop:4}}>{t.status} · {t.results.length} строк результатов</Text>
          {t.results.map((r,i) => <View key={i} style={{borderTopWidth:1, borderTopColor:COLORS.line, paddingTop:8, marginTop:8}}>
            <Text style={{fontSize:13, color:COLORS.ink, fontWeight:'800'}}>{r.place ? r.place + '. ' : ''}{r.player || r.name || 'Результат'}</Text>
            <Text style={{fontSize:12, color:COLORS.muted, marginTop:2}}>{r.category || ''}{r.score ? ' · ' + r.score : ''}{r.note ? ' · ' + r.note : ''}</Text>
            {r.members ? <Text style={{fontSize:11, color:COLORS.muted, marginTop:2}}>Состав: {r.members}</Text> : null}
          </View>)}
          <Pressable onPress={() => openSource(t.source)} style={{marginTop:12, paddingTop:10}}>
            <Text style={{fontSize:12, color:COLORS.green, fontWeight:'800'}}>Открыть источник ↗</Text>
          </Pressable>
        </View>)}
      </>}
      {tab === 'Клубы' && <>
        <Text style={{fontSize:24, fontWeight:'900', color:COLORS.ink, marginBottom:8}}>Гольф-клубы и площадки</Text>
        <Text style={{fontSize:13, color:COLORS.muted, lineHeight:20, marginBottom:16}}>Каталог собран из клубных и федерационных источников. Ссылки ведут на сайты клубов, если они опубликованы.</Text>
        {CLUBS.filter(c => (c.name + ' ' + c.country + ' ' + c.region).toLowerCase().includes(query.toLowerCase())).map((c,i) => <Pressable key={c.n || c.name} onPress={() => c.site && c.site !== '—' ? openSource(c.site) : null} style={{backgroundColor:COLORS.card, borderRadius:18, padding:17, marginBottom:10, borderWidth:1, borderColor:COLORS.line}}>
          <Text style={{fontSize:11, color:COLORS.green, fontWeight:'800'}}>{c.country} · {c.region}</Text>
          <Text style={{fontSize:17, color:COLORS.ink, fontWeight:'900', marginTop:5}}>{c.name}</Text>
          <Text style={{fontSize:12, color:COLORS.muted, marginTop:4}}>{c.type || 'Гольф-площадка'} · {c.channelStatus || ''}</Text>
          {c.note ? <Text style={{fontSize:12, color:COLORS.muted, marginTop:6, lineHeight:18}}>{c.note}</Text> : null}
          {c.site && c.site !== '—' ? <Text style={{fontSize:12, color:COLORS.green, marginTop:10, fontWeight:'700'}}>Открыть сайт ↗</Text> : null}
        </Pressable>)}
      </>}
      {tab === 'Источники' && <>
        <Text style={{fontSize:24, fontWeight:'900', color:COLORS.ink, marginBottom:8}}>Источники</Text>
        <Text style={{fontSize:13, color:COLORS.muted, lineHeight:20, marginBottom:16}}>Добавлены отдельные источники для Москвы, Санкт-Петербурга, Московской области, Краснодарского и Красноярского краёв, а также Астаны. Это реестр ссылок: автоматический ежедневный сбор ещё не запущен, а агрегаторы и архивные страницы требуют проверки у организатора.</Text>
        {SOURCES.map((s,i) => <Pressable key={s.url} onPress={() => openSource(s.url)} style={{backgroundColor:COLORS.card, borderRadius:18, padding:17, marginBottom:10, borderWidth:1, borderColor:COLORS.line}}>
          <Text style={{fontSize:11, color:COLORS.green, fontWeight:'800'}}>ИСТОЧНИК {String(i+1).padStart(2,'0')}</Text>
          <Text style={{fontSize:17, color:COLORS.ink, fontWeight:'900', marginTop:6}}>{s.name}</Text>
          <Text style={{fontSize:12, color:COLORS.muted, marginTop:4}}>{s.country} · Надёжность: {s.trust}/5</Text>
          <Text style={{fontSize:13, color:COLORS.muted, marginTop:5}}>{s.type}</Text>
          <Text style={{fontSize:12, color:COLORS.green, marginTop:10, fontWeight:'700'}}>{s.status} · Открыть ↗</Text>
        </Pressable>)}
      </>}
    </ScrollView>}

    {!selected && <View style={{position:'absolute', bottom:0, left:0, right:0, paddingHorizontal:15, paddingTop:10, paddingBottom:16, backgroundColor:'#F4F5EFEE', borderTopWidth:1, borderTopColor:COLORS.line, flexDirection:'row', justifyContent:'space-around'}}>
      {[['Турниры','▦'],['Архив','▤'],['Клубы','⌂'],['Аналитика','⌁'],['Источники','◎']].map(([name,icon]) => <Pressable key={name} onPress={() => setTab(name)} style={{alignItems:'center', minWidth:80, paddingVertical:5}}>
        <Text style={{fontSize:21, color:tab===name?COLORS.green:COLORS.muted}}>{icon}</Text>
        <Text style={{fontSize:11, fontWeight:tab===name?'900':'600', color:tab===name?COLORS.green:COLORS.muted, marginTop:3}}>{name}</Text>
      </Pressable>)}
    </View>}
  </SafeAreaView>;
}

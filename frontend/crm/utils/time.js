
export function formatDuration(seconds, lang = 'en') {
    const mins = Math.round(seconds / 60);
    const hours = Math.floor(mins / 60);
    const remainingMins = mins % 60;
  
    const labels = {
      en: { hr: 'hr', min: 'min' },
      de: { hr: 'Std.', min: 'Min.' }
    };
  
    const l = labels[lang] || labels.en;
  
    if (hours > 0 && remainingMins > 0) {
      return `${hours} ${l.hr} ${remainingMins} ${l.min}`;
    } else if (hours > 0) {
      return `${hours} ${l.hr}`;
    } else {
      return `${remainingMins} ${l.min}`;
    }
  }
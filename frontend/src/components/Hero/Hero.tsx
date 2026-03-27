import { useTranslation } from 'react-i18next';
import { Button } from '../common/Button';
import styles from './Hero.module.css';

const PLATFORM_SIGNALS = ['Google Shopping', 'Amazon', 'eBay'];

interface HeroProps {
  showPrompts: boolean;
  onPromptSelect: (prompt: string) => void;
}

export function Hero({ showPrompts, onPromptSelect }: HeroProps) {
  const { t } = useTranslation('chat');

  return (
    <section className={styles.wrap}>
      <div
        className={[
          'glass-panel',
          styles.hero,
          !showPrompts ? styles.compact : '',
        ].join(' ')}
      >
        <div className={styles.copy}>
          <p className="eyebrow">{t('hero.eyebrow')}</p>
          <h2>{t('hero.headline')}</h2>
          <p className={styles.text}>
            {t('hero.description')}
          </p>
          <div className={styles.metaRow}>
            <div className={styles.tags}>
              <span>{t('hero.features.priceCompare')}</span>
              <span>{t('hero.features.reviewInsight')}</span>
              <span>{t('hero.features.budgetDecision')}</span>
            </div>
            <div className={styles.platformStrip}>
              {PLATFORM_SIGNALS.map((platform) => (
                <span key={platform} className={styles.platformBadge}>
                  {platform}
                </span>
              ))}
              <span className={styles.platformNote}>{t('hero.platformNote')}</span>
            </div>
          </div>
        </div>
      </div>

      {showPrompts ? (
        <section className={['glass-panel', styles.prompts].join(' ')}>
          <div className={styles.promptCopy}>
            <p className="eyebrow">{t('hero.promptsTitle')}</p>
            <h3>{t('hero.promptsHeadline')}</h3>
            <p>{t('hero.promptsText')}</p>
          </div>
          <div className={styles.promptGrid}>
            {t('hero.examplePrompts', { returnObjects: true }).map((prompt: string) => (
              <Button key={prompt} variant="secondary" onClick={() => onPromptSelect(prompt)}>
                {prompt}
              </Button>
            ))}
          </div>
        </section>
      ) : null}
    </section>
  );
}

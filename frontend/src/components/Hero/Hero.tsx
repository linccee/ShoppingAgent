import { Button } from '../common/Button';
import styles from './Hero.module.css';

const EXAMPLE_PROMPTS = [
  '想买一副通勤降噪耳机，预算 ¥2000',
  '帮我比较适合游戏和办公的 27 寸显示器',
  '我想挑一台适合拍视频的手机，预算 ¥5000',
  '现在买 PS5，哪个平台更划算？',
];

interface HeroProps {
  showPrompts: boolean;
  onPromptSelect: (prompt: string) => void;
}

export function Hero({ showPrompts, onPromptSelect }: HeroProps) {
  return (
    <section className={styles.wrap}>
      <div className={['glass-panel', styles.hero].join(' ')}>
        <div className={styles.copy}>
          <p className="eyebrow">Mirror Curation · 镜澜导购</p>
          <h2>把复杂购物决策，整理成一眼就能判断的答案。</h2>
          <p className={styles.text}>
            连接 Google Shopping、Amazon 与 eBay，帮你完成比价、评论归纳与购买建议，
            在一轮对话里得到更清晰的购买判断。
          </p>
          <div className={styles.tags}>
            <span>多平台比价</span>
            <span>评论洞察</span>
            <span>预算决策</span>
          </div>
        </div>

        <div className={styles.visual}>
          <div className={styles.artShell}>
            <span className={styles.glowA} />
            <span className={styles.glowB} />
            <span className={styles.prismA} />
            <span className={styles.prismB} />
            <span className={styles.sheen} />
          </div>
          <p>为犹豫不决的购买时刻，提供更清晰的结论。</p>
        </div>
      </div>

      {showPrompts ? (
        <section className={['glass-panel', styles.prompts].join(' ')}>
          <div className={styles.promptCopy}>
            <p className="eyebrow">Curated Shopping Assistant</p>
            <h3>从“想买点什么”到“应该买哪一个”，只差一次更清晰的对话。</h3>
            <p>告诉我预算、使用场景或偏好，我会整理平台价格、评论信号与最终建议。</p>
          </div>
          <div className={styles.promptGrid}>
            {EXAMPLE_PROMPTS.map((prompt) => (
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

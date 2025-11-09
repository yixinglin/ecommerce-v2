import { Button } from "antd";
import { MailOutlined } from "@ant-design/icons";

interface EmailButtonProps {
    /** 收件人地址（必填） */
    to: string | string[];
    /** 邮件主题 */
    subject: string;
    /** 邮件正文 */
    body: string;
    /** 抄送 */
    cc?: string | string[];
    /** 密送 */
    bcc?: string | string[];
    /** 按钮文字 */
    label?: string;
    /** 按钮类型（antd Button type） */
    type?: "link" | "text" | "primary" | "default" | "dashed";
}

/**
 * EmailButton
 * 点击后自动打开本地默认邮箱客户端（如 Outlook 桌面版）并填充邮件内容
 */
function EmailButton({
    subject,
    body,
    to,
    cc,
    bcc,
    label = "Send Email",
    type = "primary",
}: EmailButtonProps) {

    const handleClick = () => {
        const toParam = Array.isArray(to) ? to.join(";") : to;
        const ccParam = Array.isArray(cc) ? cc.join(";") : cc;
        const bccParam = Array.isArray(bcc) ? bcc.join(";") : bcc;

        const encodedSubject = encodeURIComponent(subject);
        const encodedBody = encodeURIComponent(body);

        // 使用 mailto（桌面版邮箱）
        const mailtoLink = `mailto:${toParam}?${[
            cc ? `cc=${encodeURIComponent(ccParam!)}` : "",
            bcc ? `bcc=${encodeURIComponent(bccParam!)}` : "",
            `subject=${encodedSubject}`,
            `body=${encodedBody}`,
        ]
            .filter(Boolean)
            .join("&")}`;

        window.location.href = mailtoLink;
    };

    return (
        <Button type={type} icon={<MailOutlined />} onClick={handleClick}>
            {label}
        </Button>
    );
};

export default EmailButton;

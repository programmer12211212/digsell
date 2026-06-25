from django.utils import timezone


def generate_contract_html(project, proposal) -> str:
    return f"""
    <div class="contract">
        <h1>Freelance Shartnoma</h1>
        <p><strong>Loyiha:</strong> {project.title}</p>
        <p><strong>Mijoz:</strong> {project.client.get_full_name() or project.client.username}</p>
        <p><strong>Freelancer:</strong> {proposal.freelancer.get_full_name() or proposal.freelancer.username}</p>
        <p><strong>Summa:</strong> {proposal.bid_amount} UZS</p>
        <p><strong>Muddat:</strong> {proposal.delivery_days} kun</p>
        <p><strong>Deadline:</strong> {project.deadline.strftime('%d.%m.%Y')}</p>
        <hr>
        <p>{project.description}</p>
        <p><em>Shartnoma {timezone.now().strftime('%d.%m.%Y %H:%M')} da yaratildi.</em></p>
    </div>
    """

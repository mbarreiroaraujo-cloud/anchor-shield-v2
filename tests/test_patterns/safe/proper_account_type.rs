use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod safe_program {
    use super::*;

    pub fn process_data(ctx: Context<ProcessData>) -> Result<()> {
        let vault = &ctx.accounts.vault;
        msg!("Balance: {}", vault.balance);
        Ok(())
    }
}

/// Uses Account<'info, Vault> which automatically checks discriminator and owner.
/// This is the correct pattern — no vulnerability.
#[derive(Accounts)]
pub struct ProcessData<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,

    #[account(
        has_one = authority,
    )]
    pub vault: Account<'info, Vault>,

    /// CHECK: This is the system program
    pub system_program: Program<'info, System>,
}

#[account]
pub struct Vault {
    pub authority: Pubkey,
    pub balance: u64,
}

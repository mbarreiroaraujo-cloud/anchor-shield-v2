use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod vulnerable_program {
    use super::*;

    pub fn resize_account(ctx: Context<ResizeAccount>, new_size: u64) -> Result<()> {
        msg!("Account resized");
        Ok(())
    }
}

#[derive(Accounts)]
pub struct ResizeAccount<'info> {
    #[account(
        mut,
        realloc = 200,
        realloc::payer = payer,
        realloc::zero = false,
    )]
    pub data_account: Account<'info, DataAccount>,

    /// The payer is AccountInfo, not Signer — realloc does not verify signer
    #[account(mut)]
    pub payer: AccountInfo<'info>,

    pub system_program: Program<'info, System>,
}

#[account]
pub struct DataAccount {
    pub data: Vec<u8>,
}
